# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import six
import re
import pycoin
from . import exceptions
from . import scripts
from . import util


def string(s):
    if not isinstance(s, six.string_types):
        raise exceptions.InvalidString(s)


def hexdata(data):
    string(data)
    if not re.match("^[0-9a-f]*$", data):
        raise exceptions.InvalidHexData(data)


def wif(wif, netcode):
    string(wif)
    if not pycoin.key.validate.is_wif_valid(wif, allowable_netcodes=[netcode]):
        raise exceptions.InvalidWif(wif)


def pubkey(pubkey_hex):
    hexdata(pubkey_hex)
    sec = pycoin.serialize.h2b(pubkey_hex)
    if len(sec) != 33:  # FIXME always 33?
        raise exceptions.InvalidPubKey(pubkey_hex)


def hash160(hash_hex):
    hexdata(hash_hex)
    hash_bin = pycoin.serialize.h2b(hash_hex)
    if len(hash_bin) != 20:
        raise exceptions.InvalidHash160(hash_hex)


def integer(i):
    if not isinstance(i, six.integer_types):
        raise exceptions.InvalidString(i)


def sequence(number):
    integer(number)
    if not (0 <= number < scripts.MAX_SEQUENCE):
        raise exceptions.InvalidSequence(number)


def quantity(number):
    integer(number)
    if not (0 <= number < 2100000000000000):
        raise exceptions.InvalidQuantity(number)


def pubkey_published(pubkey_hex, control):
    pubkey(pubkey_hex)
    address = util.pubkey2address(pubkey_hex, netcode=control.netcode)
    txs = control.btctxstore.get_transactions(address)
    if len(txs) == 0:  # pubkey not on blockchain
        raise exceptions.PubKeyUnpublished(pubkey_hex)
