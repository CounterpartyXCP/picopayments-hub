# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import copy
import json
import requests
from requests.auth import HTTPBasicAuth
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import b2h, h2b
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import (
    get_deposit_payer_pubkey, get_deposit_payee_pubkey,
    get_deposit_expire_time, compile_deposit_script
)
from . import cli
from . import config
from . import terms
from . import database as db
from . import exceptions


def rpc_call(url, method, params, username=None, password=None):
    kwargs = {"headers": {'content-type': 'application/json'}}
    if username and password:
        kwargs["auth"] = HTTPBasicAuth(username, password)
    payload = {"method": method, "params": params, "jsonrpc": "2.0", "id": 0}
    response = requests.post(url, data=json.dumps(payload), **kwargs).json()
    if "result" not in response:
        raise exceptions.RpcCallFailed(payload, response)
    return response["result"]


def counterparty_call(method, params):
    return rpc_call(config.counterparty_url, method, params,
                    config.counterparty_username, config.counterparty_password)


def create_key(asset):
    secure_random_data = os.urandom(32)
    key = BIP32Node.from_master_secret(secure_random_data,
                                       netcode=config.netcode)
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
                                                 netcode=config.netcode)

    # spend secret for receive channel
    data.update(create_secret())

    # send micropayment channel
    data["send_spend_secret_hash"] = send_spend_secret_hash

    # connection
    handle = util.b2h(os.urandom(32))
    data["handle"] = handle
    data["hub_rpc_url"] = hub_rpc_url

    # FIXME add sync fee payment

    db.add_hub_connection(data)
    return {
        "handle": handle,
        "pubkey": hub_key["pubkey"],
        "spend_secret_hash": data["secret_hash"],
        "channel_terms": terms
    }


def _load_complete_connection(handle, recv_deposit_script):

    recv_ds_bin = h2b(recv_deposit_script)
    client_pubkey = get_deposit_payer_pubkey(recv_ds_bin)
    hub_pubkey = get_deposit_payee_pubkey(recv_ds_bin)
    expire_time = get_deposit_expire_time(recv_ds_bin)

    hub_conn = db.hub_connection(handle)
    assert(hub_conn is not None)

    send = db.micropayment_channel(hub_conn["send_channel_id"])
    assert(send["payer_pubkey"] == hub_pubkey)
    assert(send["payee_pubkey"] == client_pubkey)
    assert(not send["meta_complete"])

    recv = db.micropayment_channel(hub_conn["recv_channel_id"])
    assert(recv["payer_pubkey"] == client_pubkey)
    assert(recv["payee_pubkey"] == hub_pubkey)
    assert(not recv["meta_complete"])

    return hub_conn, send, recv, expire_time


def complete_connection(handle, recv_deposit_script, next_revoke_secret_hash):

    hub_conn, send, recv, expire_time = _load_complete_connection(
        handle, recv_deposit_script
    )

    send_deposit_script = b2h(compile_deposit_script(
        send["payer_pubkey"], send["payee_pubkey"],
        send["spend_secret_hash"], expire_time
    ))

    data = {
        "handle": handle,
        "expire_time": expire_time,
        "recv_channel_id": hub_conn["recv_channel_id"],
        "recv_deposit_script": recv_deposit_script,
        "recv_deposit_address": util.script2address(
            h2b(recv_deposit_script), netcode=config.netcode
        ),
        "send_channel_id": hub_conn["send_channel_id"],
        "send_deposit_script": send_deposit_script,
        "send_deposit_address": util.script2address(
            h2b(send_deposit_script), netcode=config.netcode
        ),
        "next_revoke_secret_hash": next_revoke_secret_hash,
    }

    data.update(create_secret())  # revoke secret

    db.complete_hub_connection(data)
    return {
        "deposit_script": send_deposit_script,
        "next_revoke_secret_hash": data["secret_hash"]
    }


def read_current_terms(asset):
    current_terms = terms.read().get(asset)
    if current_terms is None:
        raise exceptions.AssetNotInTerms(asset)
    return current_terms


def create_funding_address(asset):
    key = create_key(asset)
    db.add_keys([key])
    return key["address"]


def initialize(args):
    args = cli.parse(args)  # parse args
    config.load(args)  # load configuration

    # ensure root path exists
    if not os.path.exists(config.root):
        os.makedirs(config.root)

    terms.read()  # make sure terms file exists
    db.setup()  # setup and create db if needed
    return args


def update_channel_state(state, commit, revokes):
    if commit:
        state = counterparty_call("mpc_add_commit", {
            "state": state,
            "commit_rawtx": commit["rawtx"],
            "commit_script": commit["script"]
        })
    if revokes:
        state = counterparty_call("mpc_revoke_all", {
            "state": state, "secrets": revokes
        })
    return state


def _save_sync_data(cursor, handle, next_revoke_secret_hash, sends,
                    before_recv_state, after_recv_state, receive_payments,
                    send_commit_id, send_revokes, recv_id, next_revoke_secret):

    cursor.execute("BEGIN TRANSACTION;")

    # save send state
    if before_recv_state != after_recv_state:
        db.save_channel_state(recv_id, after_recv_state, cursor=cursor)

    # set next revoke secret hash from client
    db.set_next_revoke_secret_hash(handle, next_revoke_secret_hash)

    # save submitted payments
    if sends:
        db.add_payments(sends, cursor=cursor)

    # mark sent payments as received
    payment_ids = [p.pop("id") for p in receive_payments]
    db.set_payments_notified(payment_ids, cursor=cursor)

    # mark sent commit as received
    if send_commit_id:
        db.set_commit_notified(send_commit_id, cursor=cursor)

    # mark sent revokes as received
    revoke_ids = [p.pop("id") for p in send_revokes]
    db.set_revokes_notified(revoke_ids, cursor=cursor)

    # save next spend secret
    db.add_revoke_secret(recv_id, next_revoke_secret["secret_hash"],
                         next_revoke_secret["secret_value"], cursor=cursor)

    cursor.execute("COMMIT;")


def sync_hub_connection(handle, next_revoke_secret_hash,
                        sends, commit, revokes):

    cursor = db.get_cursor()

    # load receive channel
    hub_connection = db.hub_connection(handle, cursor=cursor)
    connection_terms = db.connection_terms(hub_connection["terms_id"])
    asset = hub_connection["asset"]
    recv_id = hub_connection["recv_channel_id"]
    send_id = hub_connection["send_channel_id"]
    recv_state = db.load_channel_state(recv_id, asset, cursor=cursor)

    # update receive channel state
    before_recv_state = copy.deepcopy(recv_state)
    after_recv_state = update_channel_state(recv_state, commit, revokes)

    # add sync fee payment
    sends.append({
        "payer_handle": handle,
        "payee_handle": None,  # to hub
        "amount": connection_terms["fee_sync"],
        "token": "sync_fee"
    })

    # create next spend secret
    next_revoke_secret = create_secret()

    # load unnotified
    send_commit = db.unnotified_commit(handle)
    send_revokes = db.unnotified_revokes(send_id)
    receive_payments = db.unnotified_payments(send_id)

    # save sync data
    send_commit_id = send_commit.pop("id") if send_commit else None
    _save_sync_data(cursor, handle, next_revoke_secret_hash, sends,
                    before_recv_state, after_recv_state, receive_payments,
                    send_commit_id, send_revokes, recv_id, next_revoke_secret)

    return {
        "receive": receive_payments,
        "commit": send_commit,
        "revokes": [r["revoke_secret"] for r in send_revokes],
        "next_revoke_secret_hash": next_revoke_secret["secret_hash"]
    }


def load_channel_data(handle, cursor):
    connection = db.hub_connection(handle, cursor=cursor)
    send_state = db.load_channel_state(
        connection["send_channel_id"],
        connection["asset"],
        cursor=cursor
    )
    recv_state = db.load_channel_state(
        connection["recv_channel_id"],
        connection["asset"],
        cursor=cursor
    )
    unnotified_commit = db.unnotified_commit(handle)
    return {
        "connection": connection,
        "send_state": send_state,
        "recv_state": recv_state,
        "unnotified_commit": unnotified_commit
    }


def process_payment(cursor, unprocessed):

    # load payer
    payer_handle = unprocessed["payer_handle"]
    if payer_handle:
        payer_data = load_channel_data(payer_handle, cursor)

    # load payee
    payee_handle = unprocessed["payee_handle"]
    if payee_handle:
        payee_data = load_channel_data(payee_handle, cursor)


def process_payments():
    cursor = db.get_cursor()
    for unprocessed in db.unprocessed_payments(cursor=cursor):
        with db.lock:
            process_payment(cursor, unprocessed)
