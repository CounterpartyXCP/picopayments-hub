# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
from picopayments import util
from picopayments.scripts import get_deposit_spend_secret_hash
from picopayments.scripts import get_deposit_payee_pubkey
from picopayments.scripts import get_commit_spend_secret_hash
from picopayments.scripts import get_commit_payee_pubkey
from picopayments.scripts import get_commit_revoke_secret_hash
from picopayments.channel.base import Base


class Payee(Base):

    def setup(self, payee_wif):
        with self.mutex:
            self.clear()
            self.payee_wif = payee_wif
            payee_pubkey = util.wif2pubkey(self.payee_wif)
            secret = os.urandom(32)  # secure random number
            self.spend_secret = util.b2h(secret)
            spend_secret_hash = util.b2h(util.hash160(secret))
            return payee_pubkey, spend_secret_hash

    def _validate_deposit_spend_secret_hash(self, script):
        given_spend_secret_hash = get_deposit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(self.spend_secret)
        if given_spend_secret_hash != own_spend_secret_hash:
            msg = "Incorrect spend secret hash: {0} != {1}"
            raise ValueError(msg.format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

    def _validate_deposit_payee_pubkey(self, script):
        given_payee_pubkey = get_deposit_payee_pubkey(script)
        own_payee_pubkey = util.wif2pubkey(self.payee_wif)
        if given_payee_pubkey != own_payee_pubkey:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, own_payee_pubkey
            ))

    def _assert_unopen_state(self):
        assert(self.payer_wif is None)
        assert(self.payee_wif is not None)
        assert(self.spend_secret is not None)
        assert(self.deposit_rawtx is None)
        assert(self.deposit_script_hex is None)
        assert(len(self.commits_active) == 0)
        assert(len(self.commits_revoked) == 0)

    def set_deposit(self, rawtx, script_hex):
        with self.mutex:
            self._assert_unopen_state()

            # TODO validate rawtx
            # TODO validate script
            # TODO check given script and rawtx match
            # TODO check given script is deposit script

            script = util.h2b(script_hex)
            self._validate_deposit_spend_secret_hash(script)
            self._validate_deposit_payee_pubkey(script)
            self.deposit_rawtx = rawtx
            self.deposit_script_hex = script_hex

    def request_commit(self, quantity):
        with self.mutex:
            self._validate_transfer_quantity(quantity)
            secret = util.b2h(os.urandom(32))  # secure random number
            secret_hash = util.hash160hex(secret)
            self.commits_requested.append(secret)
            return quantity, secret_hash

    def _validate_commit_secret_hash(self, script):
        given_spend_secret_hash = get_commit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(self.spend_secret)
        if given_spend_secret_hash != own_spend_secret_hash:
            msg = "Incorrect spend secret hash: {0} != {1}"
            raise ValueError(msg.format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

    def _validate_commit_payee_pubkey(self, script):
        given_payee_pubkey = get_commit_payee_pubkey(script)
        own_payee_pubkey = util.wif2pubkey(self.payee_wif)
        if given_payee_pubkey != own_payee_pubkey:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, own_payee_pubkey
            ))

    def _assert_open_state(self):
        assert(self.payer_wif is None)
        assert(self.payee_wif is not None)
        assert(self.spend_secret is not None)
        assert(self.deposit_rawtx is not None)
        assert(self.deposit_script_hex is not None)

    def set_commit(self, rawtx, script_hex):
        with self.mutex:
            self._assert_open_state()

            # TODO validate rawtx
            # TODO validate script
            # TODO validate rawtx signed by payer
            # TODO check it is for the current deposit
            # TODO check given script and rawtx match
            # TODO check given script is commit script

            script = util.h2b(script_hex)
            self._validate_commit_secret_hash(script)
            self._validate_commit_payee_pubkey(script)

            quantity = self.control.get_quantity(rawtx)
            revoke_secret_hash = get_commit_revoke_secret_hash(script)
            for revoke_secret in self.commits_requested[:]:

                # revoke secret hash must match as it would
                # otherwise break the channels reversability
                if revoke_secret_hash == util.hash160hex(revoke_secret):

                    # remove from requests
                    self.commits_requested.remove(revoke_secret)

                    # add to active
                    self._order_active()
                    self.commits_active.append({
                        "rawtx": rawtx, "script": script_hex,
                        "revoke_secret": revoke_secret
                    })
                    return self.get_transferred_amount()

            return None

    def revoke_until(self, quantity):
        with self.mutex:
            secrets = []
            self._order_active()
            for commit in reversed(self.commits_active[:]):
                if quantity < self.control.get_quantity(commit["rawtx"]):
                    secrets.append(commit["revoke_secret"])
                else:
                    break
            self.revoke_all(secrets)
            return secrets

    def close_channel(self):
        with self.mutex:
            self._assert_open_state()
            assert(len(self.commits_active) > 0)
            self._order_active()
            commit = self.commits_active[-1]
            rawtx = self.control.finalize_commit(
                self.payee_wif, commit["rawtx"],
                util.h2b(self.deposit_script_hex)
            )
            commit["rawtx"] = rawtx  # update commit
            return util.gettxid(rawtx)

    def update(self):

        if self.can_payout_recover():
            self.payout_recover()

    def can_payout_recover(self):
        pass

    def payout_recover(self):
        pass
