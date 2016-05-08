# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import json
from picopayments import util
from picopayments import control
from picopayments.channel.base import Base
from threading import RLock
import logging


_log = logging.getLogger(__name__)


class Payer(Base):

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

    def can_recover(self):
        with self.mutex:
            return (
                self.deposit_rawtx is not None and
                self.deposit_script_text is not None and
                self.is_deposit_expired()
            )

    def update(self):
        with self.mutex:

            # Regardless of state if deposit expired recover the coins!
            if self.can_recover():
                self.recover()
                return "RECOVERING"

            # Once the recover tx is confirmed the channel can be closed
            if self.state == "RECOVERING" and self.is_recover_confirmed():
                self.state = "CLOSED"
                _log.info("Recover deposit confirmed: {0}".format(
                    self.recover_rawtx
                ))
                return "CLOSED"

            return None
            # deposit confirmed, set channel state to open
            # if self.state == "DEPOSITING" and self.is_deposit_confirmed():
            #     self.state = "OPEN"

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
            IllegalStateError if not called directly after initialization.
            InsufficientFunds if not enough funds to cover requested quantity.
        """

        # TODO validate input
        # TODO validate pubkeys on blockchain (required by counterparty)

        with self.mutex:
            self.clear()
            self.payer_wif = payer_wif
            self.payer_pubkey = util.b2h(util.wif2sec(self.payer_wif))
            self.payee_pubkey = payee_pubkey
            self.spend_secret_hash = spend_secret_hash
            rawtx, script, address = self.control.deposit(
                self.payer_wif, self.payee_pubkey,
                self.spend_secret_hash, expire_time, quantity
            )
            self.deposit_rawtx = rawtx
            self.deposit_script_text = script
            self.state = "DEPOSITING"
            info = {
                "asset": self.control.asset,
                "quantity": quantity,
                "rawtx": rawtx,
                "txid": util.gettxid(rawtx),
                "script": script,
                "address": address
            }
            _log.info("Depositing funds: {0}".format(
                json.dumps(info, indent=2))
            )
            return info

    def recover(self):
        with self.mutex:
            self.recover_rawtx = self.control.recover(
                self.payer_wif, self.deposit_rawtx, self.deposit_script_text
            )
            self.state = "RECOVERING"
            _log.info("Recovering deposit: {0}".format(self.recover_rawtx))
