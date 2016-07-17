# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import copy
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import b2h, h2b
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import (
    get_deposit_payer_pubkey, get_deposit_payee_pubkey,
    get_deposit_expire_time, get_deposit_spend_secret_hash,
    compile_deposit_script
)
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


def create_secret():
    secret = util.b2h(os.urandom(32))
    return {
        "secret_value": secret,
        "secret_hash": util.hash160hex(secret)
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
    data.update(create_secret())

    # send micropayment channel
    data["send_spend_secret_hash"] = send_spend_secret_hash

    # connection
    handle = util.b2h(os.urandom(32))
    data["handle"] = handle
    data["hub_rpc_url"] = hub_rpc_url

    db.add_hub_connection(data)
    return {
        "handle": handle,
        "pubkey": hub_key["pubkey"],
        "spend_secret_hash": data["secret_hash"],
        "channel_terms": terms
    }


def _load_complete_connection(handle, recv_deposit_script,
                              send_unused_revoke_secret_hash):

    recv_ds_bin = h2b(recv_deposit_script)
    client_pubkey = get_deposit_payer_pubkey(recv_ds_bin)
    hub_pubkey = get_deposit_payee_pubkey(recv_ds_bin)
    expire_time = get_deposit_expire_time(recv_ds_bin)
    recv_spend_secret_hash = get_deposit_spend_secret_hash(recv_ds_bin)

    hub_conn = db.get_hub_connection(handle)
    assert(hub_conn is not None)

    send = db.get_micropayment_channel(hub_conn["send_channel_id"])
    assert(send["payer_pubkey"] == hub_pubkey)
    assert(send["payee_pubkey"] == client_pubkey)
    assert(not send["meta_complete"])

    recv = db.get_micropayment_channel(hub_conn["recv_channel_id"])
    assert(recv["payer_pubkey"] == client_pubkey)
    assert(recv["payee_pubkey"] == hub_pubkey)
    assert(not recv["meta_complete"])

    return hub_conn, send, recv, expire_time


def complete_connection(handle, recv_deposit_script,
                        send_unused_revoke_secret_hash):

    hub_conn, send, recv, expire_time = _load_complete_connection(
        handle, recv_deposit_script, send_unused_revoke_secret_hash
    )

    send_deposit_script = b2h(compile_deposit_script(
        send["payer_pubkey"], send["payee_pubkey"],
        send["spend_secret_hash"], expire_time
    ))

    netcode = "XTN" if cfg.testnet else "BTC"
    data = {
        "expire_time": expire_time,
        "recv_channel_id": hub_conn["recv_channel_id"],
        "recv_deposit_script": recv_deposit_script,
        "recv_deposit_address": util.script2address(
            h2b(recv_deposit_script), netcode=netcode
        ),
        "send_channel_id": hub_conn["send_channel_id"],
        "send_deposit_script": send_deposit_script,
        "send_deposit_address": util.script2address(
            h2b(send_deposit_script), netcode=netcode
        ),
        "send_unused_revoke_secret_hash": send_unused_revoke_secret_hash,
    }

    data.update(create_secret())  # revoke secret

    db.complete_hub_connection(data)
    return {
        "deposit_script": send_deposit_script,
        "unused_revoke_secret_hash": data["secret_hash"]
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
