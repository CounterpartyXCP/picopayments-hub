# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
import copy
import pyelliptic
from pycoin.serialize import b2h, h2b
from counterpartylib.lib.micropayments import util


def sign(wif, data):
    privkey = util.wif2privkey(wif)
    pubkey = util.wif2pubkey(wif)
    uncompressed_sec = util.decode_pubkey(pubkey)
    ecc = pyelliptic.ECC(
        curve="secp256k1", pubkey=uncompressed_sec, privkey=privkey
    )
    return b2h(ecc.sign(data))


def verify(pubkey, signature, data):
    uncompressed_sec = util.decode_pubkey(pubkey)
    ecc = pyelliptic.ECC(curve="secp256k1", pubkey=uncompressed_sec)
    return ecc.verify(h2b(signature), data)


def sign_json(json_data):
    wif = json_data.pop("wif")
    pubkey = util.wif2pubkey(wif)
    json_data["pubkey"] = pubkey
    data = json.dumps(json_data, sort_keys=True)
    signature = sign(wif, data)
    json_data["signature"] = signature
    assert("wif" not in json_data)
    return json_data


def verify_json(json_data):
    json_data = copy.deepcopy(json_data)
    if "pubkey" not in json_data:
        print("PUBKEY:", json_data)
    pubkey = json_data["pubkey"]
    signature = json_data.pop("signature")
    data = json.dumps(json_data, sort_keys=True)
    return verify(pubkey, signature, data)
