# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from .control import Control
from .control import DEFAULT_COUNTERPARTY_RPC_USER
from .control import DEFAULT_COUNTERPARTY_RPC_PASSWORD
from .control import DEFAULT_TESTNET


STATES = [
    "UNINITIALIZED"
]


class Base(object):

    state = "UNINITIALIZED"
    control = None
    payer_wif = None
    payer_sec = None
    payee_wif = None
    payee_sec = None
    secret = None
    deposit_tx = None   # pycoin.tx.Tx
    commit_txs = []     # [pycoin.tx.Tx]
    recover_tx = None   # pycoin.tx.Tx
    change_tx = None    # pycoin.tx.Tx


class Payer(Base):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD, url=None,
                 testnet=DEFAULT_TESTNET, dryrun=False):
        self.control = Control(self, asset=asset, user=user, password=password,
                               url=url, testnet=testnet, dryrun=dryrun)


class Payee(Base):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD, url=None,
                 testnet=DEFAULT_TESTNET, dryrun=False):
        self.control = Control(self, asset=asset, user=user, password=password,
                               url=url, testnet=testnet, dryrun=dryrun)
