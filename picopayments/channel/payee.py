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
                 api_url=None, testnet=control.DEFAULT_TESTNET, dryrun=False,
                 auto_update_interval=0):

        # TODO validate input
        # TODO validate pubkey on blockchain (required by counterparty)

        self.control = control.Control(
            asset, user=user, password=password, api_url=api_url,
            testnet=testnet, dryrun=dryrun, fee=control.DEFAULT_TXFEE,
            dust_size=control.DEFAULT_DUSTSIZE
        )

        self.payee_wif = payee_wif
        self.payee_pubkey = util.b2h(util.wif2sec(self.payee_wif))

        secret = os.urandom(32)
        self.spend_secret = util.b2h(secret)
        self.state = "INITIALIZING"

        self.mutex = RLock()
        if auto_update_interval > 0:
            self.interval = auto_update_interval
            self.start()

    def update(self):
        pass
