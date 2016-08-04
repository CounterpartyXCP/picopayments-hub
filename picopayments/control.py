# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
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
from . import config
from . import terms
from . import database as db
from . import exceptions


def rpc_call(url, method, params, username=None, password=None, verify=True):
    payload = {"method": method, "params": params, "jsonrpc": "2.0", "id": 0}

    kwargs = {
        "url": url,
        "headers": {'content-type': 'application/json'},
        "data": json.dumps(payload),
        "verify": verify,
    }
    if username and password:
        kwargs["auth"] = HTTPBasicAuth(username, password)
    response = requests.post(**kwargs).json()
    if "result" not in response:
        raise exceptions.RpcCallFailed(payload, response)
    return response["result"]


def counterparty_call(method, params):
    return rpc_call(
        config.counterparty_url, method, params,
        username=config.counterparty_username,
        password=config.counterparty_password
    )


def create_key(asset, netcode="BTC"):
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

    # current terms and asset
    data = {"asset": asset}
    terms = read_current_terms(asset)
    data.update(terms)

    # new hub key
    hub_key = create_key(asset, netcode=config.netcode)
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
    key = create_key(asset, netcode=config.netcode)
    db.add_keys([key])
    return key["address"]


def initialize(args):
    config.load(args)  # load configuration

    # ensure root path exists
    if not os.path.exists(config.root):
        os.makedirs(config.root)

    terms.read()  # make sure terms file exists
    db.setup()  # setup and create db if needed


def update_channel_state(channel_id, asset, commit=None,
                         revokes=None, cursor=None):

    state = db.load_channel_state(channel_id, asset, cursor=cursor)
    unnotified_revokes = db.unnotified_revokes(channel_id, cursor=None)
    unnotified_commit = db.unnotified_commit(channel_id, cursor=cursor)
    if commit is not None:
        state = counterparty_call("mpc_add_commit", {
            "state": state,
            "commit_rawtx": commit["rawtx"],
            "commit_script": commit["script"]
        })
    if revokes is not None:
        state = counterparty_call("mpc_revoke_all", {
            "state": state, "secrets": revokes
        })
    db.save_channel_state(
        channel_id, state, unnotified_commit=unnotified_commit,
        unnotified_revokes=unnotified_revokes, cursor=cursor
    )
    return state


def _save_sync_data(cursor, handle, next_revoke_secret_hash,
                    receive_payments, send_commit_id, send_revokes,
                    recv_id, next_revoke_secret):

    cursor.execute("BEGIN TRANSACTION;")

    # set next revoke secret hash from client
    db.set_next_revoke_secret_hash(handle, next_revoke_secret_hash)

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

    # update channels state
    update_channel_state(recv_id, asset, commit=commit, cursor=cursor)
    update_channel_state(send_id, asset, revokes=revokes, cursor=cursor)

    # add sync fee payment
    sends.insert(0, {
        "payer_handle": handle,
        "payee_handle": None,  # to hub
        "amount": connection_terms["fee_sync"],
        "token": "sync_fee"
    })

    # process payments
    for send in sends:
        process_payment(cursor, send)

    # create next spend secret
    next_revoke_secret = create_secret()

    # load unnotified
    send_commit = db.unnotified_commit(handle)
    send_revokes = db.unnotified_revokes(send_id)
    receive_payments = db.unnotified_payments(send_id)

    # save sync data
    send_commit_id = send_commit.pop("id") if send_commit else None
    _save_sync_data(cursor, handle, next_revoke_secret_hash,
                    receive_payments, send_commit_id, send_revokes,
                    recv_id, next_revoke_secret)

    return {
        "receive": receive_payments,
        "commit": send_commit,
        "revokes": [r["revoke_secret"] for r in send_revokes],
        "next_revoke_secret_hash": next_revoke_secret["secret_hash"]
    }


def load_channel_data(handle, cursor):
    connection = db.hub_connection(handle, cursor=cursor)
    send_state = db.load_channel_state(connection["send_channel_id"],
                                       connection["asset"], cursor=cursor)
    send_deposit_address = util.script2address(
        util.h2b(send_state["deposit_script"]), netcode=config.netcode
    )
    recv_state = db.load_channel_state(connection["recv_channel_id"],
                                       connection["asset"], cursor=cursor)
    recv_deposit_address = util.script2address(
        util.h2b(send_state["deposit_script"]), netcode=config.netcode
    )
    send_transferred = counterparty_call("mpc_transferred_amount", {
        "state": send_state
    })
    send_deposit_amount = counterparty_call("get_balances", {"filters": [
        {'field': 'address', 'op': '==', 'value': send_deposit_address},
        {'field': 'asset', 'op': '==', 'value': connection["asset"]},
    ]})[0]["quantity"]
    recv_transferred = counterparty_call("mpc_transferred_amount", {
        "state": recv_state
    })
    recv_deposit_amount = counterparty_call("get_balances", {"filters": [
        {'field': 'address', 'op': '==', 'value': recv_deposit_address},
        {'field': 'asset', 'op': '==', 'value': connection["asset"]},
    ]})[0]["quantity"]
    unnotified_commit = db.unnotified_commit(handle, cursor=cursor)
    send_payments_sum = db.send_payments_sum(handle, cursor=cursor)
    recv_payments_sum = db.recv_payments_sum(handle, cursor=cursor)
    transferred_amount = recv_transferred - send_transferred
    payments_sum = send_payments_sum - recv_payments_sum

    # sendable (what this channel can send to another)
    sendable_amount = transferred_amount - payments_sum

    # receivable (what this channel can receive from another)
    receivable_potential = send_deposit_amount + recv_transferred
    receivable_owed = (abs(payments_sum) if payments_sum < 0 else 0)
    receivable_amount = receivable_potential - receivable_owed
    return {
        "connection": connection,
        "send_state": send_state,
        "send_transferred_amount": send_transferred,
        "send_payments_sum": send_payments_sum,
        "send_deposit_amount": send_deposit_amount,
        "recv_state": recv_state,
        "recv_transferred_amount": recv_transferred,
        "recv_payments_sum": recv_payments_sum,
        "recv_deposit_amount": recv_deposit_amount,
        "transferred_amount": transferred_amount,
        "payments_sum": payments_sum,
        "unnotified_commit": unnotified_commit,
        "sendable_amount": sendable_amount,
        "receivable_amount": receivable_amount,
    }


def process_payment(cursor, payment):

    # load payer
    payer_handle = payment["payer_handle"]
    payer = load_channel_data(payer_handle, cursor)

    # check payer has enough funds or can revoke sends until enough available
    if payment["amount"] > payer["sendable_amount"]:
        raise exceptions.PaymentExceedsSpendable(
            payment["amount"], payer["sendable_amount"], payment["token"]
        )

    # load payee
    payee_handle = payment["payee_handle"]
    if payee_handle:

        payee = load_channel_data(payee_handle, cursor)
        if payment["amount"] > payee["receivable_amount"]:
            raise exceptions.PaymentExceedsReceivable(
                payment["amount"], payee["receivable_amount"], payment["token"]
            )

        cursor.execute("BEGIN TRANSACTION;")

        # TODO adjust payee channel

    # fee payment
    else:
        cursor.execute("BEGIN TRANSACTION;")

    db.add_payment(payment, cursor=cursor)
    cursor.execute("COMMIT;")
