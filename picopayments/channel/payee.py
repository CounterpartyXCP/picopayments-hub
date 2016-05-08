# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import logging
from threading import RLock
from picopayments import util
from picopayments import control
from picopayments.channel.base import Base


_log = logging.getLogger(__name__)


class Payee(Base):

    def __init__(self, payee_wif, asset,
                 user=control.DEFAULT_COUNTERPARTY_RPC_USER,
                 password=control.DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=control.DEFAULT_TESTNET, dryrun=False):

        # TODO validate input
        # TODO validate pubkey on blockchain (required by counterparty)

        self.control = control.Control(
            asset, user=user, password=password, api_url=api_url,
            testnet=testnet, dryrun=dryrun, fee=control.DEFAULT_TXFEE,
            dust_size=control.DEFAULT_DUSTSIZE
        )

        self.payee_wif = payee_wif
        self.spend_secret = os.urandom(32)
        self.state = "INITIALIZING"

        self.mutex = RLock()
        self.interval = 10
        self.start()

    def update(self):
        pass

    def get_pubkey(self):
        with self.mutex:
            return util.b2h(util.wif2sec(self.payee_wif))

    def get_secret_hash(self):
        with self.mutex:
            return util.b2h(util.hash160(self.spend_secret))
