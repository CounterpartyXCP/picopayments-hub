# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import copy
import pycoin
from threading import RLock
from picopayments import util
from picopayments import control
from picopayments import validate
from picopayments.scripts import get_commit_revoke_secret_hash


class Base(util.UpdateThreadMixin):

    state = {
        "payer_wif": None,
        "payee_wif": None,
        "spend_secret": None,
        "deposit_script": None,
        "deposit_rawtx": None,
        "expire_rawtxs": [],  # ["rawtx", ...]
        "change_rawtxs": [],  # ["rawtx", ...]
        "revoke_rawtxs": [],  # ["rawtx", ...]
        "payout_rawtxs": [],  # ["rawtx", ...]

        # Quantity not needed as payer may change it. If its heigher its
        # against our self intrest to throw away money. If its lower it
        # gives us a better resolution when reversing the channel.
        "commits_requested": [],  # ["revoke_secret_hex"]

        # must be ordered lowest to heighest at all times!
        "commits_active": [],     # [{
        #                             "rawtx": hex,
        #                             "script": hex,
        #                             "revoke_secret": hex
        #                         }]

        "commits_revoked": [],    # [{
        #                            "rawtx": hex,  # unneeded?
        #                            "script": hex,
        #                            "revoke_secret": hex
        #                         }]
    }

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
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self._order_active()
            return copy.deepcopy(self.state)

    def load(self, state):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self.state = copy.deepcopy(state)
            return self

    def clear(self):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self.state = {
                "payer_wif": None,
                "payee_wif": None,
                "spend_secret": None,
                "deposit_script": None,
                "deposit_rawtx": None,
                "expire_rawtxs": [],
                "change_rawtxs": [],
                "payout_rawtxs": [],
                "revoke_rawtxs": [],
                "commits_requested": [],
                "commits_active": [],
                "commits_revoked": []
            }

    def _get_confirms(self, rawtx):
        txid = util.gettxid(rawtx)
        confirms = self.control.btctxstore.confirms(txid)
        print("Confirms {0} {1}".format(txid, confirms))
        return confirms or 0

    def _get_deposit_confirms(self):
        assert(self.state["deposit_rawtx"] is not None)
        assert(self.state["deposit_script"] is not None)
        return self._get_confirms(self.state["deposit_rawtx"])

    def is_deposit_confirmed(self, minconfirms=1):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            validate.unsigned(minconfirms)
            script = util.h2b(self.state["deposit_script"])
            if self.control.get_script_balance(script) == (0, 0):
                return False
            return self._get_deposit_confirms() >= minconfirms

    def get_transferred_amount(self):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            if len(self.state["commits_active"]) == 0:
                return 0
            self._order_active()
            commit = self.state["commits_active"][-1]
            return self.control.get_quantity(commit["rawtx"])

    def _get_deposit_total(self):
        assert(self.state["deposit_rawtx"] is not None)
        return self.control.get_quantity(self.state["deposit_rawtx"])

    def _validate_transfer_quantity(self, quantity):
        transferred = self.get_transferred_amount()
        if quantity <= transferred:
            msg = "Amount not greater transferred: {0} <= {1}"
            raise ValueError(msg.format(quantity, transferred))

        total = self._get_deposit_total()
        if quantity > total:
            msg = "Amount greater total: {0} > {1}"
            raise ValueError(msg.fromat(quantity, total))

    def _order_active(self):

        def sort_func(entry):
            return self.control.get_quantity(entry["rawtx"])
        self.state["commits_active"].sort(key=sort_func)

    def _revoke(self, secret):
        with self.mutex:
            secret_hash = util.hash160hex(secret)
            for commit in self.state["commits_active"][:]:
                script = util.h2b(commit["script"])
                if secret_hash == get_commit_revoke_secret_hash(script):
                    self.state["commits_active"].remove(commit)
                    commit["revoke_secret"] = secret  # save secret
                    self.state["commits_revoked"].append(commit)
                    return copy.deepcopy(commit)
            return None

    def revoke_all(self, secrets):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            return list(map(self._revoke, secrets))

    def _all_confirmed(self, rawtxs, minconfirms=1):
        validate.unsigned(minconfirms)
        if len(rawtxs) == 0:
            return False
        for rawtx in rawtxs:
            confirms = self._get_confirms(rawtx)
            if confirms < minconfirms:
                return False
        return True

    def _commit_spent(self, commit):
        txid = util.gettxid(commit["rawtx"])
        for rawtx in (self.state["payout_rawtxs"] +
                      self.state["revoke_rawtxs"] +
                      self.state["change_rawtxs"] +
                      self.state["expire_rawtxs"]):
            tx = pycoin.tx.Tx.from_hex(rawtx)
            for txin in tx.txs_in:
                if util.b2h_rev(txin.previous_hash) == txid:
                    print("found spent:", txid)
                    return True
        return False
