# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
from . import util
from . import control


VALID_STATES = [
    "INITIALIZING",  # deposit not yet made
    "DEPOSITING",  # deposit made but not yet confirmed
    "OPEN",  # deposit made, confirmed but not commit tx ready
    "CLOSED",  # no more funds in channel
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
    deposit_rawtx = None
    deposit_script_text = None  # disassembled script
    recover_rawtx = None

    # commit_txs = []     # [pycoin.tx.Tx]
    # recover_tx = None   # pycoin.tx.Tx
    # change_tx = None    # pycoin.tx.Tx

    def _validate_state(self, expected):
        assert(expected in VALID_STATES)
        if self.state != expected:
            raise IllegalStateError(expected, self.state)

    def is_deposit_expired(self):
        assert(self.deposit_rawtx is not None)
        assert(self.deposit_script_text is not None)

        return False  # TODO implement


class Payer(Base):

    def __init__(self, payer_wif, payee_pubkey, spend_secret_hash,
                 expire_time, asset, user=control.DEFAULT_COUNTERPARTY_RPC_USER,
                 password=control.DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=control.DEFAULT_TESTNET, dryrun=False):

        # TODO validate input
        # TODO validate pubkeys on blockchain (required by counterparty)

        self.control = control.Control(asset, user=user, password=password,
                                       api_url=api_url, testnet=testnet,
                                       dryrun=dryrun, fee=control.DEFAULT_TXFEE,
                                       dust_size=control.DEFAULT_DUSTSIZE)

        self.payer_wif = payer_wif
        self.payee_pubkey = payee_pubkey
        self.spend_secret_hash = spend_secret_hash
        self.expire_time = expire_time
        self.state = "INITIALIZING"

        # TODO make thread that check if deposit was confirmed
        #      and change state from DEPOSITING to OPEN

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
        asset_balance, btc_balance = self.control.get_balance(address)
        if asset_balance < quantity:
            raise InsufficientFunds(quantity, asset_balance)

        # FIXME check if enough btc for fees or catch counterparty error
        # FIXME check if channel previously used

        rawtx, script = self.control.deposit(self.payer_wif, self.payee_pubkey,
                                             self.spend_secret_hash,
                                             self.expire_time, quantity)
        self.deposit_rawtx = rawtx
        self.deposit_script_text = script
        self.state = "DEPOSITING"
        return rawtx, script

    def recover(self):
        self._validate_state("OPEN")
        # FIXME check if deposit tx has enough confirms to recover

        rawtx = self.control.recover(self.payer_wif, self.deposit_rawtx,
                                     self.deposit_script_text)
        self.recover_rawtx = rawtx
        self.state = "CLOSED"
        return rawtx


class Payee(Base):

    def __init__(self, payee_wif, asset,
                 user=control.DEFAULT_COUNTERPARTY_RPC_USER,
                 password=control.DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=control.DEFAULT_TESTNET, dryrun=False):

        # TODO validate input
        # TODO validate pubkey on blockchain (required by counterparty)

        self.control = control.Control(asset, user=user, password=password,
                                       api_url=api_url, testnet=testnet,
                                       dryrun=dryrun, fee=control.DEFAULT_TXFEE,
                                       dust_size=control.DEFAULT_DUSTSIZE)

        self.payee_wif = payee_wif
        self.spend_secret = os.urandom(32)
        self.state = "INITIALIZING"

    def get_pubkey(self):
        return util.b2h(util.wif2sec(self.payee_wif))

    def get_secret_hash(self):
        return util.b2h(util.hash160(self.spend_secret))
