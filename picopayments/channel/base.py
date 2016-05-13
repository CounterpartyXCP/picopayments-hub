# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from threading import RLock
from picopayments import util
from picopayments import scripts
from picopayments import control


class Base(util.UpdateThreadMixin):

    payer_wif = None
    payee_wif = None
    spend_secret = None
    deposit_script_hex = None
    deposit_rawtx = None
    timeout_rawtx = None
    change_rawtx = None
    active_commits = []
    revoked_commits = []

    # {
    #   "txid": hex,
    #   "rawtx": hex,
    #   "amount": int,
    #   "script": hex,
    #   "revoke_secret": hex,
    #   "revoke_secret_hash": hex,
    # }

    def __init__(self, asset, user=control.DEFAULT_COUNTERPARTY_RPC_USER,
                 password=control.DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=control.DEFAULT_TESTNET, dryrun=False,
                 auto_update_interval=0):

        # TODO validate input

        self.control = control.Control(
            asset, user=user, password=password, api_url=api_url,
            testnet=testnet, dryrun=dryrun, fee=control.DEFAULT_TXFEE,
            dust_size=control.DEFAULT_DUSTSIZE
        )

        self.mutex = RLock()
        if auto_update_interval > 0:
            self.interval = auto_update_interval
            self.start()

    def commits_peek(self, stack):
        if len(stack) == 0:
            return None
        return stack[-1]

    def save(self):
        with self.mutex:
            return {
                "payer_wif": self.payer_wif,
                "payee_wif": self.payee_wif,
                "spend_secret": self.spend_secret,
                "deposit_script_hex": self.deposit_script_hex,
                "deposit_rawtx": self.deposit_rawtx,
                "timeout_rawtx": self.timeout_rawtx,
                "change_rawtx": self.change_rawtx,
                "active_commits": self.active_commits,
                "revoked_commits": self.revoked_commits,
            }

    def load(self, data):
        # TODO validate input
        with self.mutex:
            self.payer_wif = data["payer_wif"]
            self.payee_wif = data["payee_wif"]
            self.spend_secret = data["spend_secret"]
            self.deposit_script_hex = data["deposit_script_hex"]
            self.deposit_rawtx = data["deposit_rawtx"]
            self.timeout_rawtx = data["timeout_rawtx"]
            self.change_rawtx = data["change_rawtx"]
            self.active_commits = data["active_commits"]
            self.revoked_commits = data["revoked_commits"]

    def clear(self):
        with self.mutex:
            self.payer_wif = None
            self.payee_wif = None
            self.spend_secret = None
            self.deposit_script_hex = None
            self.deposit_rawtx = None
            self.timeout_rawtx = None
            self.change_rawtx = None
            self.active_commits = []
            self.revoked_commits = []

    def get_deposit_confirms(self):
        with self.mutex:
            assert(self.deposit_rawtx is not None)
            assert(self.deposit_script_hex is not None)
            txid = util.gettxid(self.deposit_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def get_timeout_confirms(self):
        with self.mutex:
            assert(self.timeout_rawtx is not None)
            txid = util.gettxid(self.timeout_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def get_change_confirms(self):
        with self.mutex:
            assert(self.change_rawtx is not None)
            txid = util.gettxid(self.change_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def get_spend_secret_hash(self):
        if self.spend_secret is not None:  # payee
            return util.b2h(util.hash160(util.h2b(self.spend_secret)))
        elif self.deposit_script_hex is not None:  # payer
            script = util.h2b(self.deposit_script_hex)
            return scripts.get_deposit_spend_secret_hash(script)
        else:  # undefined
            raise Exception("Undefined state, not payee or payer.")

    def is_deposit_confirmed(self):
        with self.mutex:
            return self.get_deposit_confirms() > 0

    def is_deposit_expired(self):
        with self.mutex:
            script = util.h2b(self.deposit_script_hex)
            t = scripts.get_deposit_expire_time(script)
            return self.get_deposit_confirms() >= t

    def is_timeout_confirmed(self):
        with self.mutex:
            assert(self.timeout_rawtx is not None)
            txid = util.gettxid(self.timeout_rawtx)
            return bool(self.control.btctxstore.confirms(txid))

    def is_change_confirmed(self):
        with self.mutex:
            assert(self.change_rawtx is not None)
            txid = util.gettxid(self.change_rawtx)
            return bool(self.control.btctxstore.confirms(txid))

    def is_closing(self):
        return (
            self.change_rawtx is not None and not self.is_change_confirmed() or
            self.timeout_rawtx is not None and not self.is_timeout_confirmed()
        )

    def is_closed(self):
        return (
            self.change_rawtx is not None and self.is_change_confirmed() or
            self.timeout_rawtx is not None and self.is_timeout_confirmed()
        )

    def set_spend_secret(self, secret):
        self.spend_secret = secret

    def set_deposit(self, deposit_rawtx, deposit_script_hex):

        # FIXME validate input

        # assert correct state
        assert(self.payer_wif is None)
        assert(self.payee_wif is not None)
        assert(self.spend_secret is not None)
        assert(self.spend_secret_hash is not None)
        assert(self.deposit_rawtx is None)
        assert(self.deposit_script_hex is None)
        assert(len(self.active_commits) == 0)
        assert(len(self.revoked_commits) == 0)

        script = util.h2b(deposit_script_hex)

        # deposit script must have the correct spend secret hash
        given_spend_secret_hash = scripts.get_deposit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(self.spend_secret)
        if given_spend_secret_hash != own_spend_secret_hash:
            raise ValueError("Incorrect spend secret hash: {0} != {1}".format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

        # FIXME get payer pubkey

        self.deposit_rawtx = deposit_rawtx
        self.deposit_script_hex = deposit_script_hex
