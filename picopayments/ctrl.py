# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import b2h
from . import cli
from . import cfg
from . import terms
from . import db


def rpc_call(url, method, params, username=None, password=None):
    kwargs = {"headers": {'content-type': 'application/json'}}
    if username and password:
        kwargs["auth"] = HTTPBasicAuth(username, password)
    payload = {"method": method, "params": params, "jsonrpc": "2.0", "id": 0}
    response = requests.post(url, data=json.dumps(payload), **kwargs).json()
    if "result" not in response:
        raise Exception("Rpc call failed! {0} -> {1}".format(payload, response))
    return response["result"]


def counterparty_call(method, params):
    return rpc_call(cfg.counterparty_url, method, params,
                    cfg.counterparty_username, cfg.counterparty_password)


def create_key(asset):
    netcode = "XTN" if cfg.testnet else "BTC"
    secure_random_data = os.urandom(256)
    key = BIP32Node.from_master_secret(secure_random_data, netcode=netcode)
    return {
        "asset": asset,
        "pubkey": b2h(key.sec()),
        "wif": key.wif(),
        "address": key.address(),
    }


def get_fund_address(asset):
    print(json.dumps(db.get_keys(), indent=2))
    # entries = db.get_keys(asset=asset)
    # FIXME return key with least funds
    # return entries[0]


def fill_key_pool(terms_data):
    entries = db.count_keys()
    for asset in terms_data.keys():
        count = entries.get(asset, 0)
        if count < cfg.key_pool_size:
            needed = cfg.key_pool_size - count
            db.add_keys([create_key(asset) for i in range(needed)])


def initialize():
    args = cli.parse(sys.argv[1:])  # parse args
    cfg.load(args)  # load configuration
    terms_data = terms.read()  # make sure terms file exists
    db.initialize()  # create db and migrate if needed
    fill_key_pool(terms_data)
    return args
