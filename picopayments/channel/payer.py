# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments import util
from picopayments import validate
from picopayments import exceptions
from picopayments import scripts
from picopayments.channel.base import Base
from picopayments.scripts import get_deposit_expire_time


class Payer(Base):

    def can_expire_recover(self):
        with self.mutex:
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

    def update(self):
        with self.mutex:

            # If revoked commit published, recover funds asap!
            revokable = self.get_revoke_recoverable()
            if len(revokable) > 0:
                self.revoke_recover(revokable)

            # If spend secret exposed by payout, recover change!
            if self.can_change_recover():
                spend_secret = self.find_spend_secret()
                if spend_secret is not None:
                    self.change_recover(spend_secret)

            # If deposit expired recover the coins!
            if self.can_expire_recover():
                self.expire_recover()

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

    def expire_recover(self):
        with self.mutex:
            script = util.h2b(self.state["deposit_script"])
            rawtx = self.control.expire_recover(
                self.state["payer_wif"], script
            )
            self.state["expire_rawtxs"].append(rawtx)

    def find_spend_secret(self):
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

    def can_change_recover(self):
        with self.mutex:
            script = util.h2b(self.state["deposit_script"])
            return self.control.can_spend_from_script(script)

    def change_recover(self, spend_secret):
        with self.mutex:
            script = util.h2b(self.state["deposit_script"])
            rawtx = self.control.change_recover(
                self.state["payer_wif"], script, spend_secret
            )
            self.state["change_rawtxs"].append(rawtx)

    def create_commit(self, quantity, revoke_secret_hash, delay_time):
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

    def get_revoke_recoverable(self):
        with self.mutex:
            revokable = []  # (secret, script)
            for commit in self.state["commits_revoked"]:
                script = util.h2b(commit["script"])
                address = util.script2address(
                    script, netcode=self.control.netcode
                )
                if self.control.can_spend_from_address(address):
                    revokable.append((script, commit["revoke_secret"]))
            return revokable

    def revoke_recover(self, revokable):
        with self.mutex:
            for script, secret in revokable:
                rawtx = self.control.revoke_recover(
                    self.state["payer_wif"], script, secret
                )
                self.state["revoke_rawtxs"].append(rawtx)

    def change_confirmed(self, minconfirms=1):
        with self.mutex:
            validate.unsigned(minconfirms)
            return self._all_confirmed(self.state["change_rawtxs"],
                                       minconfirms=minconfirms)
