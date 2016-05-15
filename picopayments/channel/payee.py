# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
from picopayments import util
from picopayments.scripts import get_deposit_spend_secret_hash
from picopayments.scripts import get_deposit_payee_pubkey
from picopayments.channel.base import Base


class Payee(Base):

    def setup(self, payee_wif):
        with self.mutex:
            self.clear()
            self.payee_wif = payee_wif
            payee_pubkey = util.wif2pubkey(self.payee_wif)
            secret = os.urandom(32)  # secure random number
            self.spend_secret = util.b2h(secret)
            self.spend_secret_hash = util.b2h(util.hash160(secret))
            return payee_pubkey, self.spend_secret_hash

    def set_deposit(self, deposit_rawtx, deposit_script_hex):
        with self.mutex:

            # FIXME validate input

            # assert correct state
            assert(self.payer_wif is None)
            assert(self.payee_wif is not None)
            assert(self.spend_secret is not None)
            assert(self.spend_secret_hash is not None)
            assert(self.deposit_rawtx is None)
            assert(self.deposit_script_hex is None)

            assert(len(self.commits_active) == 0)
            assert(len(self.commits_revoked) == 0)

            script = util.h2b(deposit_script_hex)

            # deposit script must have the correct spend secret hash
            given_spend_secret_hash = get_deposit_spend_secret_hash(script)
            own_spend_secret_hash = util.hash160hex(self.spend_secret)
            if given_spend_secret_hash != own_spend_secret_hash:
                msg = "Incorrect spend secret hash: {0} != {1}"
                raise ValueError(msg.format(
                    given_spend_secret_hash, own_spend_secret_hash
                ))

            # deposit mush have the correct payee pubkey
            given_payee_pubkey = get_deposit_payee_pubkey(script)
            own_payee_pubkey = util.wif2pubkey(self.payee_wif)
            if given_payee_pubkey != own_payee_pubkey:
                msg = "Incorrect payee pubkey: {0} != {1}"
                raise ValueError(msg.format(
                    given_payee_pubkey, own_payee_pubkey
                ))

            self.deposit_rawtx = deposit_rawtx
            self.deposit_script_hex = deposit_script_hex

    def request_commit(self, quantity):
        with self.mutex:
            self.validate_transfer_quantity(quantity)

            secret = util.b2h(os.urandom(32))  # secure random number
            secret_hash = util.hash160hex(secret)

            # add request to pending
            self.commits_pending.append((quantity, secret))

            return quantity, secret_hash

    def update(self):
        pass
