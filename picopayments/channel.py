# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import copy
import pycoin
from threading import RLock
from picopayments import util
from picopayments import control
from picopayments import validate
from picopayments.scripts import get_commit_revoke_secret_hash
from picopayments.scripts import get_deposit_spend_secret_hash
from picopayments.scripts import get_deposit_payee_pubkey
from picopayments.scripts import get_commit_spend_secret_hash
from picopayments.scripts import get_commit_payee_pubkey
from picopayments.scripts import get_commit_delay_time
from picopayments import exceptions
from picopayments import scripts
from picopayments.scripts import get_deposit_expire_time


class Channel(util.UpdateThreadMixin):

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

    def setup(self, payee_wif):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self.clear()
            self.state["payee_wif"] = payee_wif
            payee_pubkey = util.wif2pubkey(self.state["payee_wif"])
            secret = os.urandom(32)  # secure random number
            self.state["spend_secret"] = util.b2h(secret)
            spend_secret_hash = util.b2h(util.hash160(secret))
            return payee_pubkey, spend_secret_hash

    def _validate_deposit_spend_secret_hash(self, script):
        given_spend_secret_hash = get_deposit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(self.state["spend_secret"])
        if given_spend_secret_hash != own_spend_secret_hash:
            msg = "Incorrect spend secret hash: {0} != {1}"
            raise ValueError(msg.format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

    def _validate_deposit_payee_pubkey(self, script):
        given_payee_pubkey = get_deposit_payee_pubkey(script)
        own_payee_pubkey = util.wif2pubkey(self.state["payee_wif"])
        if given_payee_pubkey != own_payee_pubkey:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, own_payee_pubkey
            ))

    def _assert_unopen_state(self):
        assert(self.state["payer_wif"] is None)
        assert(self.state["payee_wif"] is not None)
        assert(self.state["spend_secret"] is not None)
        assert(self.state["deposit_rawtx"] is None)
        assert(self.state["deposit_script"] is None)
        assert(len(self.state["commits_active"]) == 0)
        assert(len(self.state["commits_revoked"]) == 0)

    def _validate_payer_deposit(self, rawtx, script_hex):
        tx = pycoin.tx.Tx.from_hex(rawtx)
        assert(tx.bad_signature_count() == 1)

        # TODO validate script
        # TODO check given script and rawtx match
        # TODO check given script is deposit script

    def _validate_payer_commit(self, rawtx, script_hex):
        tx = pycoin.tx.Tx.from_hex(rawtx)
        assert(tx.bad_signature_count() == 1)

        # TODO validate script
        # TODO validate rawtx signed by payer
        # TODO check it is for the current deposit
        # TODO check given script and rawtx match
        # TODO check given script is commit script

    def set_deposit(self, rawtx, script_hex):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self._assert_unopen_state()
            self._validate_payer_deposit(rawtx, script_hex)

            script = util.h2b(script_hex)
            self._validate_deposit_spend_secret_hash(script)
            self._validate_deposit_payee_pubkey(script)
            self.state["deposit_rawtx"] = rawtx
            self.state["deposit_script"] = script_hex

    def request_commit(self, quantity):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self._validate_transfer_quantity(quantity)
            secret = util.b2h(os.urandom(32))  # secure random number
            secret_hash = util.hash160hex(secret)
            self.state["commits_requested"].append(secret)
            return quantity, secret_hash

    def _validate_commit_secret_hash(self, script):
        given_spend_secret_hash = get_commit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(self.state["spend_secret"])
        if given_spend_secret_hash != own_spend_secret_hash:
            msg = "Incorrect spend secret hash: {0} != {1}"
            raise ValueError(msg.format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

    def _validate_commit_payee_pubkey(self, script):
        given_payee_pubkey = get_commit_payee_pubkey(script)
        own_payee_pubkey = util.wif2pubkey(self.state["payee_wif"])
        if given_payee_pubkey != own_payee_pubkey:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, own_payee_pubkey
            ))

    def set_commit(self, rawtx, script_hex):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self._validate_payer_commit(rawtx, script_hex)

            script = util.h2b(script_hex)
            self._validate_commit_secret_hash(script)
            self._validate_commit_payee_pubkey(script)

            revoke_secret_hash = get_commit_revoke_secret_hash(script)
            for revoke_secret in self.state["commits_requested"][:]:

                # revoke secret hash must match as it would
                # otherwise break the channels reversability
                if revoke_secret_hash == util.hash160hex(revoke_secret):

                    # remove from requests
                    self.state["commits_requested"].remove(revoke_secret)

                    # add to active
                    self._order_active()
                    self.state["commits_active"].append({
                        "rawtx": rawtx, "script": script_hex,
                        "revoke_secret": revoke_secret
                    })
                    return self.get_transferred_amount()

            return None

    def revoke_until(self, quantity):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            secrets = []
            self._order_active()
            for commit in reversed(self.state["commits_active"][:]):
                if quantity < self.control.get_quantity(commit["rawtx"]):
                    secrets.append(commit["revoke_secret"])
                else:
                    break
            list(map(self._revoke, secrets))

            return secrets

    def close_channel(self):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            assert(len(self.state["commits_active"]) > 0)
            self._order_active()
            commit = self.state["commits_active"][-1]
            rawtx = self.control.finalize_commit(
                self.state["payee_wif"], commit["rawtx"],
                util.h2b(self.state["deposit_script"])
            )
            commit["rawtx"] = rawtx  # update commit
            return util.gettxid(rawtx)

    def payee_update(self):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:

            # payout recoverable commits
            scripts = self._get_payout_recoverable()
            if len(scripts) > 0:
                self._payout_recover(scripts)

    def _get_payout_recoverable(self):
        scripts = []
        for commit in (self.state["commits_active"] +
                       self.state["commits_revoked"]):
            script = util.h2b(commit["script"])
            delay_time = get_commit_delay_time(script)
            address = util.script2address(
                script, netcode=self.control.netcode
            )
            if self._commit_spent(commit):
                continue
            if self.control.can_spend_from_address(address):
                utxos = self.control.btctxstore.retrieve_utxos([address])
                for utxo in utxos:
                    txid = utxo["txid"]
                    confirms = self.control.btctxstore.confirms(txid)
                    if confirms >= delay_time:
                        print("spendable commit address:", address)
                        scripts.append(script)
        return scripts

    def _payout_recover(self, scripts):
        for script in scripts:
            rawtx = self.control.payout_recover(
                self.state["payee_wif"], script, self.state["spend_secret"]
            )
            self.state["payout_rawtxs"].append(rawtx)

    def payout_confirmed(self, minconfirms=1):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            validate.unsigned(minconfirms)
            return self._all_confirmed(self.state["payout_rawtxs"],
                                       minconfirms=minconfirms)

    def _can_expire_recover(self):
        return (
            # we know the payer wif
            self.state["payer_wif"] is not None and

            # deposit was made
            self.state["deposit_rawtx"] is not None and
            self.state["deposit_script"] is not None and

            # deposit expired
            self._is_deposit_expired() and

            # funds to recover
            self._can_deposit_spend()
        )

    def _can_deposit_spend(self):
        script = util.h2b(self.state["deposit_script"])
        return self.control.can_spend_from_script(script)

    def _is_deposit_expired(self):
        script = util.h2b(self.state["deposit_script"])
        t = get_deposit_expire_time(script)
        return self._get_deposit_confirms() >= t

    def payer_update(self):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:

            # If revoked commit published, recover funds asap!
            revokable = self._get_revoke_recoverable()
            if len(revokable) > 0:
                self._revoke_recover(revokable)

            # If spend secret exposed by payout, recover change!
            if self._can_change_recover():
                spend_secret = self._find_spend_secret()
                if spend_secret is not None:
                    self._change_recover(spend_secret)

            # If deposit expired recover the coins!
            if self._can_expire_recover():
                self._expire_recover()

    def _validate_deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                          expire_time, quantity):

        # validate untrusted input data
        validate.wif(payer_wif, self.control.netcode)
        validate.pubkey(payee_pubkey)
        validate.hash160(spend_secret_hash)
        validate.sequence(expire_time)
        validate.quantity(quantity)

        # get balances
        address = util.wif2address(payer_wif)
        asset_balance, btc_balance = self.control.get_address_balance(address)

        # check asset balance
        if asset_balance < quantity:
            raise exceptions.InsufficientFunds(quantity, asset_balance)

        # check btc balance
        extra_btc = (self.control.fee + self.control.dust_size) * 3
        if btc_balance < extra_btc:
            raise exceptions.InsufficientFunds(extra_btc, btc_balance)

    def deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                expire_time, quantity):
        """Create deposit for given quantity.

        Args:
            payer_wif: TODO doc string
            payee_pubkey: TODO doc string
            spend_secret_hash: TODO doc string
            expire_time: TODO doc string
            quantity: In satoshis

        Returns:
            Transaction ID for the created deposit.

        Raises:
            ValueError if invalid quantity
            InsufficientFunds if not enough funds to cover requested quantity.
        """
        # FIXME add doc string
        # FIXME validate all input

        with self.mutex:
            self._validate_deposit(payer_wif, payee_pubkey, spend_secret_hash,
                                   expire_time, quantity)

            self.clear()
            self.state["payer_wif"] = payer_wif
            rawtx, script = self.control.deposit(
                self.state["payer_wif"], payee_pubkey,
                spend_secret_hash, expire_time, quantity
            )
            self.state["deposit_rawtx"] = rawtx
            self.state["deposit_script"] = util.b2h(script)
            return {"rawtx": rawtx, "script": util.b2h(script)}

    def _expire_recover(self):
        script = util.h2b(self.state["deposit_script"])
        rawtx = self.control.expire_recover(
            self.state["payer_wif"], script
        )
        self.state["expire_rawtxs"].append(rawtx)

    def _find_spend_secret(self):
        for commit in self.state["commits_active"] + \
                self.state["commits_revoked"]:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.control.netcode
            )
            txs = self.control.btctxstore.get_transactions(address)
            if len(txs) == 1:
                continue  # only the commit, no payout
            for txid in txs:
                rawtx = self.control.btctxstore.retrieve_tx(txid)
                spend_secret = scripts.get_spend_secret(rawtx, script)
                if spend_secret is not None:
                    return spend_secret
        return None

    def _can_change_recover(self):
        script = util.h2b(self.state["deposit_script"])
        return self.control.can_spend_from_script(script)

    def _change_recover(self, spend_secret):
        script = util.h2b(self.state["deposit_script"])
        rawtx = self.control.change_recover(
            self.state["payer_wif"], script, spend_secret
        )
        self.state["change_rawtxs"].append(rawtx)

    def create_commit(self, quantity, revoke_secret_hash, delay_time):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            self._validate_transfer_quantity(quantity)
            rawtx, script = self.control.create_commit(
                self.state["payer_wif"], util.h2b(self.state["deposit_script"]),
                quantity, revoke_secret_hash, delay_time
            )
            script_hex = util.b2h(script)
            self._order_active()
            self.state["commits_active"].append({
                "rawtx": rawtx, "script": script_hex, "revoke_secret": None
            })
            return {"rawtx": rawtx, "script": script_hex}

    def _get_revoke_recoverable(self):
        revokable = []  # (secret, script)
        for commit in self.state["commits_revoked"]:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.control.netcode
            )
            if self.control.can_spend_from_address(address):
                revokable.append((script, commit["revoke_secret"]))
        return revokable

    def _revoke_recover(self, revokable):
        for script, secret in revokable:
            rawtx = self.control.revoke_recover(
                self.state["payer_wif"], script, secret
            )
            self.state["revoke_rawtxs"].append(rawtx)

    def change_confirmed(self, minconfirms=1):
        # FIXME add doc string
        # FIXME validate all input
        with self.mutex:
            validate.unsigned(minconfirms)
            return self._all_confirmed(self.state["change_rawtxs"],
                                       minconfirms=minconfirms)
