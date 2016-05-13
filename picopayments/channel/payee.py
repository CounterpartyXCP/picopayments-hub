# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
from picopayments import util
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

    def request(self, amount):
        with self.mutex:
            secret = util.b2h(os.urandom(32))  # secure random number
            secret_hash = util.hash160hex(secret)

            # TODO check current commits
            # TODO add new commit entry

            return amount, secret_hash

    def update(self):
        pass
