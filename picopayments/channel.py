# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


STATES = [
]

EVENT_TYPES = [
]


class ChannelPayer(object):

    state = "UNINITIALIZED"
    wallet_self = None    # wif
    wallet_other = None   # sec
    recover_self = None   # wif
    recover_other = None  # sec
    anchor_tx = None      # pycoin.tx.Tx
    commit_tx_self = []   # {"tx": tx, "secret": six.binary_type}
    commit_tx_other = []  # {"tx": tx, "secret": six.binary_type}


class ChannelPayee(object):
    pass


class Channel(object):
    pass
