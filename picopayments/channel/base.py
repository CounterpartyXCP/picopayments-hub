# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import copy
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

    # Quantity not needed as payer may change it. If its heigher its against
    # our self intrest to throw away money. If its lower it gives us a better
    # resolution when reversing the channel.
    commits_requested = []  # ["revoke_secret_hex"]

    commits_active = []     # [{
    #                             "rawtx": hex,
    #                             "script": hex,
    #                             "revoke_secret": hex
    #                         }]

    commits_revoked = []    # [{
    #                            "rawtx": hex,
    #                            "script": hex,
    #                            "revoke_secret": hex
    #                         }]

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

    def save(self):
        with self.mutex:
            return copy.deepcopy({
                "payer_wif": self.payer_wif,
                "payee_wif": self.payee_wif,
                "spend_secret": self.spend_secret,
                "deposit_script_hex": self.deposit_script_hex,
                "deposit_rawtx": self.deposit_rawtx,
                "timeout_rawtx": self.timeout_rawtx,
                "change_rawtx": self.change_rawtx,
                "commits_requested": self.commits_requested,
                "commits_active": self.commits_active,
                "commits_revoked": self.commits_revoked,
            })

    def load(self, data):
        # TODO validate input
        data = copy.deepcopy(data)
        with self.mutex:
            self.payer_wif = data["payer_wif"]
            self.payee_wif = data["payee_wif"]
            self.spend_secret = data["spend_secret"]
            self.deposit_script_hex = data["deposit_script_hex"]
            self.deposit_rawtx = data["deposit_rawtx"]
            self.timeout_rawtx = data["timeout_rawtx"]
            self.change_rawtx = data["change_rawtx"]
            self.commits_requested = data["commits_requested"]
            self.commits_active = data["commits_active"]
            self.commits_revoked = data["commits_revoked"]

    def clear(self):
        with self.mutex:
            self.payer_wif = None
            self.payee_wif = None
            self.spend_secret = None
            self.deposit_script_hex = None
            self.deposit_rawtx = None
            self.timeout_rawtx = None
            self.change_rawtx = None
            self.commits_requested = []
            self.commits_active = []
            self.commits_revoked = []

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
        with self.mutex:
            unconfirmed_change = (
                self.change_rawtx is not None and
                not self.is_change_confirmed()
            )
            unconfirmed_timeout = (
                self.timeout_rawtx is not None and
                not self.is_timeout_confirmed()
            )
            return unconfirmed_change or unconfirmed_timeout

    def is_closed(self):
        with self.mutex:
            return (
                self.change_rawtx is not None and self.is_change_confirmed() or
                self.timeout_rawtx is not None and self.is_timeout_confirmed()
            )

    def set_spend_secret(self, secret):
        with self.mutex:
            self.spend_secret = secret

    def get_transferred_amount(self):
        """Returns funds transferred from payer to payee."""
        with self.mutex:
            # FIXME sort first!
            heighest = util.stack_peek(self.commits_active)
            if heighest is not None:
                return self.control.get_quantity(heighest["rawtx"])
            return 0

    def get_deposit_total(self):
        """Returns the total deposit amount"""
        with self.mutex:
            assert(self.deposit_rawtx is not None)
            return self.control.get_quantity(self.deposit_rawtx)

    def get_deposit_remaining(self):
        """Returns the remaining deposit amount"""
        with self.mutex:
            return self.get_deposit_total() - self.get_transferred_amount()

    def validate_transfer_quantity(self, quantity):
        with self.mutex:

            transferred = self.get_transferred_amount()
            if quantity <= transferred:
                msg = "Amount not greater transferred: {0} <= {1}"
                raise ValueError(msg.format(quantity, transferred))

            total = self.get_deposit_total()
            if quantity > total:
                msg = "Amount greater total: {0} > {1}"
                raise ValueError(msg.fromat(quantity, total))
