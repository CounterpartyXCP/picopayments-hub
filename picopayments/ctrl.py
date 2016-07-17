# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import copy
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import b2h
from counterpartylib.lib.micropayments import util
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
        raise Exception(
            "Rpc call failed! {0} -> {1}".format(payload, response))
    return response["result"]


def counterparty_call(method, params):
    return rpc_call(cfg.counterparty_url, method, params,
                    cfg.counterparty_username, cfg.counterparty_password)


def create_key(asset):
    netcode = "XTN" if cfg.testnet else "BTC"
    secure_random_data = os.urandom(32)
    key = BIP32Node.from_master_secret(secure_random_data, netcode=netcode)
    return {
        "asset": asset,
        "pubkey": b2h(key.sec()),
        "wif": key.wif(),
        "address": key.address(),
    }


def create_hub_connection(asset, client_pubkey,
                          send_spend_secret_hash, hub_rpc_url):
    netcode = "XTN" if cfg.testnet else "BTC"

    # current terms and asset
    data = {"asset": asset}
    terms = read_current_terms(asset)
    data.update(terms)

    # new hub key
    hub_key = create_key(asset)
    data["hub_wif"] = hub_key["wif"]
    data["hub_pubkey"] = hub_key["pubkey"]
    data["hub_address"] = hub_key["address"]

    # client key
    data["client_pubkey"] = client_pubkey
    data["client_address"] = util.pubkey2address(client_pubkey,
                                                 netcode=netcode)

    # spend secret for receive channel
    recv_spend_secret = util.b2h(os.urandom(32))
    recv_spend_secret_hash = util.hash160hex(recv_spend_secret)
    data["secret_value"] = recv_spend_secret
    data["secret_hash"] = recv_spend_secret_hash

    # send micropayment channel
    data["send_spend_secret_hash"] = send_spend_secret_hash

    # connection
    channel_handle = util.b2h(os.urandom(32))
    data["handle"] = channel_handle
    data["hub_rpc_url"] = hub_rpc_url

    db.add_hub_connection(data)
    return {
        "channel_handle": channel_handle,
        "pubkey": hub_key["pubkey"],
        "spend_secret_hash": recv_spend_secret_hash,
        "channel_terms": terms
    }


def read_current_terms(asset):
    current_terms = terms.read().get(asset)
    if current_terms is None:
        raise Exception("No terms for given asset: {0}".format(asset))
    return current_terms


def create_funding_address(asset):
    key = create_key(asset)
    db.add_keys([key])
    return key["address"]


def initialize(args):
    args = cli.parse(args)  # parse args
    cfg.load(args)  # load configuration
    terms.read()  # make sure terms file exists
    db.setup()  # setup and create db if needed
    return args
