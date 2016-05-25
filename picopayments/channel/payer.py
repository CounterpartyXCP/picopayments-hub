# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments import util
from picopayments import validate
from picopayments import exceptions
from picopayments import scripts
from picopayments.channel.base import Base


class Payer(Base):

    def can_expire_recover(self):
        with self.mutex:
            return (
                # we know the payer wif
                self.payer_wif is not None and

                # deposit was made
                self.deposit_rawtx is not None and
                self.deposit_script_hex is not None and

                # deposit expired
                self.is_deposit_expired() and

                # not already recovering
                not self.is_closing()
            )

    def update(self):
        with self.mutex:

            # If revoked commit published, recover funds asap!
            revokable = self.get_revoke_recoverable()
            if len(revokable) > 0:
                self.revoke_recover(revokable)

            # If deposit expired recover the coins!
            if self.can_expire_recover():
                self.expire_recover()

            # If spend secret exposed recover the coins!
            spend_secret = self.find_spend_secret()
            if spend_secret is not None:
                self.change_recover(spend_secret)

    def _validate_deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                          expire_time, quantity):

        # validate untrusted input data
        validate.wif(payer_wif, self.control.netcode)
        validate.pubkey(payee_pubkey)
        validate.hash160(spend_secret_hash)
        validate.sequence(expire_time)
        validate.quantity(quantity)

        # get balances
        payer_address = util.wif2address(payer_wif)
        asset_balance, btc_balance = self.control.get_balance(payer_address)

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
            self.payer_wif = payer_wif
            rawtx, script = self.control.deposit(
                self.payer_wif, payee_pubkey,
                spend_secret_hash, expire_time, quantity
            )
            self.deposit_rawtx = rawtx
            self.deposit_script_hex = util.b2h(script)
            return {"rawtx": rawtx, "script": util.b2h(script)}

    def expire_recover(self):
        with self.mutex:
            script = util.h2b(self.deposit_script_hex)
            self.expire_rawtx = self.control.expire_recover(
                self.payer_wif, script
            )

    def find_spend_secret(self):
        for commit in self.commits_active + self.commits_revoked:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.control.netcode
            )
            txs = self.control.btctxstore.get_transactions(address)
            # if len(txs) == 1:
            #     continue  # only the commit, no payout
            for txid in txs:
                rawtx = self.control.btctxstore.retrieve_tx(txid)
                spend_secret = scripts.get_spend_secret(rawtx, script)
                if spend_secret is not None:
                    return spend_secret
        return None

    def change_recover(self, spend_secret):
        with self.mutex:
            script = util.h2b(self.deposit_script_hex)
            self.change_rawtx = self.control.change_recover(
                self.payer_wif, script, spend_secret
            )

    def create_commit(self, quantity, revoke_secret_hash, delay_time):
        with self.mutex:
            self._validate_transfer_quantity(quantity)
            rawtx, script = self.control.create_commit(
                self.payer_wif, util.h2b(self.deposit_script_hex),
                quantity, revoke_secret_hash, delay_time
            )
            script_hex = util.b2h(script)
            self._order_active()
            self.commits_active.append({
                "rawtx": rawtx, "script": script_hex, "revoke_secret": None
            })
            return {"rawtx": rawtx, "script": script_hex}

    def get_revoke_recoverable(self):
        with self.mutex:
            revokable = []  # (secret, script)
            for commit in self.commits_revoked:
                script = util.h2b(commit["script"])
                address = util.script2address(
                    script, netcode=self.control.netcode
                )
                utxos = self.control.btctxstore.retrieve_utxos([address])
                if len(utxos) > 0:
                    revokable.append((script, commit["revoke_secret"]))
            return revokable

    def revoke_recover(self, revokable):
        with self.mutex:
            for script, secret in revokable:
                rawtx = self.control.revoke_recover(
                    self.payer_wif, script, secret
                )
                self.revoke_rawtxs.append(rawtx)
