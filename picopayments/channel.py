# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
from . import util
from .control import Control
from .control import DEFAULT_COUNTERPARTY_RPC_USER
from .control import DEFAULT_COUNTERPARTY_RPC_PASSWORD
from .control import DEFAULT_TESTNET


VALID_STATES = [
    "INITIALIZING",
]


class IllegalStateError(Exception):

    def __init__(self, expected, got):
        msg = "Expected state '{0}' instead of '{1}'"
        super(IllegalStateError, self).__init__(msg.format(expected, got))


class InsufficientFunds(Exception):

    def __init__(self, needed, available):
        msg = "Needed funds '{0}', available '{1}'"
        super(InsufficientFunds, self).__init__(msg.format(needed, available))


class Base(object):

    state = None
    # deposit_tx = None   # pycoin.tx.Tx
    # commit_txs = []     # [pycoin.tx.Tx]
    # recover_tx = None   # pycoin.tx.Tx
    # change_tx = None    # pycoin.tx.Tx

    def _validate_state(self, expected):
        assert(expected in VALID_STATES)
        if self.state != expected:
            raise IllegalStateError(expected, self.state)


class Payer(Base):

    def __init__(self, payer_wif, payee_pubkey, spend_secret_hash,
                 expire_time, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 counterparty_url=None, testnet=DEFAULT_TESTNET, dryrun=False):

        # TODO validate input
        # TODO validate pubkeys on blockchain (required by counterparty)

        self.control = Control(asset, user=user, password=password,
                               counterparty_url=counterparty_url,
                               testnet=testnet, dryrun=dryrun)
        self.payer_wif = payer_wif
        self.payee_pubkey = payee_pubkey
        self.spend_secret_hash = spend_secret_hash
        self.expire_time = expire_time
        self.state = "INITIALIZING"

    def deposit(self, quantity):
        """Create deposit for given quantity.

        Args:
            quantity: In satoshis

        Returns:
            Transaction ID for the created deposit.

        Raises:
            IllegalStateError if not called directly after initialization.
            InsufficientFunds if not enough funds to cover requested quantity.
        """
        self._validate_state("INITIALIZING")
        if quantity <= 0:
            raise ValueError()

        # check if enough asset funds to make the deposit
        address = util.wif2address(self.payer_wif)
        result = self.control.get_balance(address)
        available = result[0]["quantity"]
        if available < quantity:
            raise InsufficientFunds(quantity, available)

        # FIXME check if enough btc for fees
        # FIXME check if channel previously used

        return self.control.deposit(self.payer_wif, self.payee_pubkey,
                                    self.spend_secret_hash,
                                    self.expire_time, quantity)


class Payee(Base):

    def __init__(self, payee_wif, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 counterparty_url=None, testnet=DEFAULT_TESTNET, dryrun=False):

        # TODO validate input
        # TODO validate pubkey on blockchain (required by counterparty)

        self.control = Control(asset, user=user, password=password,
                               counterparty_url=counterparty_url,
                               testnet=testnet, dryrun=dryrun)

        self.payee_wif = payee_wif
        self.spend_secret = os.urandom(32)
        self.state = "INITIALIZING"

    def get_pubkey(self):
        return util.b2h(util.wif2sec(self.payee_wif))

    def get_secret_hash(self):
        return util.b2h(util.hash160(self.spend_secret))
