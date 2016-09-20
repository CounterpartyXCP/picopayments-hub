# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import copy
import json
import pkg_resources
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import b2h
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments import scripts
from picopayments import rpc
from picopayments import usr
from picopayments import db
from picopayments import auth
from picopayments import err
from picopayments import etc
from picopayments import log
from picopayments import sql


_TERMS_FP = pkg_resources.resource_stream("picopayments", "terms.json")
TERMS = json.loads(_TERMS_FP.read().decode("utf-8"))


def get_secret(secret_hash):
    return db.get_secret(hash=secret_hash)["value"]


def get_wif(pubkey):
    return db.key(pubkey=pubkey)["wif"]


def create_key(asset, netcode="BTC"):
    secure_random_data = os.urandom(32)
    key = BIP32Node.from_master_secret(secure_random_data, netcode=netcode)
    return {
        "asset": asset, "pubkey": b2h(key.sec()),
        "wif": key.wif(), "address": key.address(),
    }


def create_secret():
    secret = util.b2h(os.urandom(32))
    return {"secret_value": secret, "secret_hash": util.hash160hex(secret)}


def create_hub_connection(asset, client_pubkey,
                          h2c_spend_secret_hash, hub_rpc_url):

    # current terms and asset
    data = {"asset": asset}
    current_terms = terms().get(asset)
    data.update(current_terms)

    # new hub key
    hub_key = create_key(asset, netcode=etc.netcode)
    data["hub_wif"] = hub_key["wif"]
    data["hub_pubkey"] = hub_key["pubkey"]
    data["hub_address"] = hub_key["address"]

    # client key
    data["client_pubkey"] = client_pubkey
    data["client_address"] = util.pubkey2address(client_pubkey,
                                                 netcode=etc.netcode)

    # spend secret for receive channel
    data.update(create_secret())

    # send micropayment channel
    data["h2c_spend_secret_hash"] = h2c_spend_secret_hash

    # connection
    handle = util.b2h(os.urandom(32))
    data["handle"] = handle
    data["hub_rpc_url"] = hub_rpc_url

    db.add_hub_connection(data)
    log.info("Created connection {0}".format(handle))
    return (
        {
            "handle": handle,
            "spend_secret_hash": data["secret_hash"],
            "channel_terms": current_terms
        },
        hub_key["wif"]
    )


def _load_incomplete_connection(handle, c2h_deposit_script_hex):

    client_pubkey = scripts.get_deposit_payer_pubkey(c2h_deposit_script_hex)
    hub_pubkey = scripts.get_deposit_payee_pubkey(c2h_deposit_script_hex)
    expire_time = scripts.get_deposit_expire_time(c2h_deposit_script_hex)

    hub_conn = db.hub_connection(handle=handle)
    assert(hub_conn is not None)
    assert(not hub_conn["complete"])

    h2c = db.micropayment_channel(id=hub_conn["h2c_channel_id"])
    assert(h2c["payer_pubkey"] == hub_pubkey)
    assert(h2c["payee_pubkey"] == client_pubkey)

    c2h = db.micropayment_channel(id=hub_conn["c2h_channel_id"])
    assert(c2h["payer_pubkey"] == client_pubkey)
    assert(c2h["payee_pubkey"] == hub_pubkey)

    hub_key = db.key(pubkey=hub_pubkey)

    return hub_conn, h2c, expire_time, hub_key


def complete_connection(handle, c2h_deposit_script,
                        next_revoke_secret_hash):

    hub_conn, h2c, expire_time, hub_key = _load_incomplete_connection(
        handle, c2h_deposit_script
    )

    h2c_deposit_script = scripts.compile_deposit_script(
        h2c["payer_pubkey"], h2c["payee_pubkey"],
        h2c["spend_secret_hash"], expire_time
    )

    data = {
        "handle": handle,
        "expire_time": expire_time,
        "c2h_channel_id": hub_conn["c2h_channel_id"],
        "c2h_deposit_script": c2h_deposit_script,
        "c2h_deposit_address": util.script2address(
            c2h_deposit_script, netcode=etc.netcode
        ),
        "h2c_channel_id": hub_conn["h2c_channel_id"],
        "h2c_deposit_script": h2c_deposit_script,
        "h2c_deposit_address": util.script2address(
            h2c_deposit_script, netcode=etc.netcode
        ),
        "next_revoke_secret_hash": next_revoke_secret_hash,
    }

    data.update(create_secret())  # revoke secret

    db.complete_hub_connection(data)
    log.info("Completed connection {0}".format(handle))
    return (
        {
            "deposit_script": h2c_deposit_script,
            "next_revoke_secret_hash": data["secret_hash"]
        },
        hub_key["wif"]
    )


def find_key_with_funds(asset, asset_quantity, btc_quantity):
    btc_quantity = btc_quantity + util.get_fee_multaple(
        factor=1, fee_per_kb=etc.fee_per_kb,
        regular_dust_size=etc.regular_dust_size
    )
    nearest = {"key": None, "available": 2100000000000000}
    for key in db.keys(asset=asset):
        address = key["address"]
        if has_unconfirmed_transactions(address):
            continue  # ignore if unconfirmed inputs/outputs
        available = get_balance(address, asset)
        # FIXME check btc quantity
        if available < asset_quantity:
            continue  # not enough funds
        if nearest["available"] > available:
            nearest = {"key": key, "available": available}
    return nearest["key"]


def get_funding_addresses(assets):
    addresses = {}
    for asset in assets:
        key = create_key(asset, netcode=etc.netcode)
        db.add_keys([key])
        addresses[asset] = key["address"]
    return addresses


def initialize(args):
    etc.load(args)  # load configuration

    # ensure basedir path exists
    if not os.path.exists(etc.basedir):
        os.makedirs(etc.basedir)

    terms()  # make sure terms file exists
    db.setup()  # setup and create db if needed
    log.info("Basedir: {0}".format(etc.basedir))  # make sure log file exists


def update_channel_state(channel_id, asset, commit=None,
                         revokes=None, cursor=None):

    state = db.load_channel_state(channel_id, asset, cursor=cursor)
    unnotified_revokes = db.unnotified_revokes(channel_id=channel_id)
    unnotified_commit = db.unnotified_commit(channel_id=channel_id,
                                             cursor=cursor)
    unnotified_revoke_secrets = [x["revoke_secret"]
                                 for x in unnotified_revokes]
    if commit is not None:
        state = rpc.cplib.mpc_add_commit(
            state=state,
            commit_rawtx=commit["rawtx"],
            commit_script=commit["script"]
        )
    if revokes is not None:
        # FIXME will not set revokes as unnotified
        #       currently not a problem as its only used for hub to client
        #       but its begging to be missused!!
        state = rpc.cplib.mpc_revoke_all(state=state, secrets=revokes)
    cursor.execute("BEGIN TRANSACTION;")
    db.save_channel_state(
        channel_id, state, unnotified_commit=unnotified_commit,
        unnotified_revoke_secrets=unnotified_revoke_secrets, cursor=cursor
    )
    cursor.execute("COMMIT;")
    return state


def _save_sync_data(cursor, handle, next_revoke_secret_hash,
                    receive_payments, h2c_commit_id, h2c_revokes,
                    c2h_id, next_revoke_secret):

    cursor.execute("BEGIN TRANSACTION;")

    # set next revoke secret hash from client
    db.set_next_revoke_secret_hash(
        handle=handle, next_revoke_secret_hash=next_revoke_secret_hash
    )

    # mark sent payments as received
    payment_ids = [{"id": p.pop("id")} for p in receive_payments]
    db.set_payments_notified(payment_ids, cursor=cursor)

    # mark sent commit as received
    if h2c_commit_id:
        db.set_commit_notified(id=h2c_commit_id, cursor=cursor)

    # mark sent revokes as received
    revoke_ids = [p.pop("id") for p in h2c_revokes]
    db.set_revokes_notified(revoke_ids, cursor=cursor)

    # save next spend secret
    db.add_revoke_secret(c2h_id, next_revoke_secret["secret_hash"],
                         next_revoke_secret["secret_value"], cursor=cursor)

    cursor.execute("COMMIT;")


def sync_hub_connection(handle, next_revoke_secret_hash,
                        sends, commit, revokes):

    cursor = sql.get_cursor()

    # load receive channel
    hub_connection = db.hub_connection(handle=handle, cursor=cursor)
    connection_terms = db.terms(id=hub_connection["terms_id"])
    asset = hub_connection["asset"]
    c2h_id = hub_connection["c2h_channel_id"]
    h2c_id = hub_connection["h2c_channel_id"]

    # update channels state
    update_channel_state(c2h_id, asset, commit=commit, cursor=cursor)
    update_channel_state(h2c_id, asset, revokes=revokes, cursor=cursor)

    # add sync fee payment
    sends.insert(0, {
        "payee_handle": None,  # to hub
        "amount": connection_terms["sync_fee"],
        "token": "sync_fee"
    })

    # process payments
    for payment in sends:
        process_payment(handle, cursor, payment)

    # create next spend secret
    next_revoke_secret = create_secret()

    # load unnotified
    h2c_commit = db.unnotified_commit(channel_id=h2c_id)
    c2h_revokes = db.unnotified_revokes(channel_id=c2h_id)
    receive_payments = db.unnotified_payments(payee_handle=handle)

    # save sync data
    h2c_commit_id = None
    if h2c_commit:
        h2c_commit_id = h2c_commit.pop("id")
    _save_sync_data(
        cursor, handle, next_revoke_secret_hash, receive_payments,
        h2c_commit_id, c2h_revokes, c2h_id, next_revoke_secret
    )

    hub_key = db.channel_payer_key(id=h2c_id)
    return (
        {
            "receive": receive_payments,
            "commit": h2c_commit,
            "revokes": [r["revoke_secret"] for r in c2h_revokes],
            "next_revoke_secret_hash": next_revoke_secret["secret_hash"]
        },
        hub_key["wif"]
    )


def get_balance(address, asset):
    results = rpc.cplib.get_balances(filters=[
        {'field': 'address', 'op': '==', 'value': address},
        {'field': 'asset', 'op': '==', 'value': asset},
    ])
    return results[0]["quantity"] if results else 0


def deposit_address(state):
    return get_script_address(state["deposit_script"])


def get_script_address(script):
    return util.script2address(script, netcode=etc.netcode)


def get_transferred_quantity(state):
    return rpc.cplib.mpc_transferred_amount(state=state)


def is_expired(state, clearance):
    return rpc.cplib.mpc_deposit_expired(state=state, clearance=clearance)


def get_tx(txid):
    return rpc.cplib.getrawtransaction(tx_hash=txid)


def publish(rawtx, dryrun=False):
    if dryrun:
        return util.gettxid(rawtx)
    return rpc.cplib.sendrawtransaction(tx_hex=rawtx)  # pragma: no cover


def send_funds(destination, asset, quantity, dryrun=False):
    extra_btc = util.get_fee_multaple(
        factor=3, fee_per_kb=etc.fee_per_kb,
        regular_dust_size=etc.regular_dust_size
    )
    key = find_key_with_funds(asset, quantity, extra_btc)
    if key is None:
        raise err.InsufficientFunds(asset, quantity)
    unsigned_rawtx = rpc.cplib.create_send(
        source=key["address"], destination=destination, asset=asset,
        regular_dust_size=extra_btc, disable_utxo_locks=True, quantity=quantity
    )
    signed_rawtx = scripts.sign_deposit(get_tx, key["wif"], unsigned_rawtx)
    return publish(signed_rawtx, dryrun=dryrun)


def get_transactions(address):
    return rpc.cplib.search_raw_transactions(address=address, unconfirmed=True)


def has_unconfirmed_transactions(address):
    transactions = get_transactions(address)
    for transaction in transactions:
        if transaction.get("confirmations", 0) == 0:
            return True
    return False


def load_connection_data(handle, cursor):
    connection = db.hub_connection(handle=handle, cursor=cursor)
    terms = db.terms(id=connection["terms_id"], cursor=cursor)
    h2c_state = db.load_channel_state(
        connection["h2c_channel_id"], connection["asset"], cursor=cursor
    )
    h2c_deposit_address = deposit_address(h2c_state)
    c2h_state = db.load_channel_state(
        connection["c2h_channel_id"], connection["asset"], cursor=cursor
    )
    c2h_deposit_address = deposit_address(c2h_state)
    h2c_transferred = get_transferred_quantity(h2c_state)
    h2c_deposit_amount = get_balance(h2c_deposit_address, connection["asset"])
    c2h_transferred = get_transferred_quantity(c2h_state)
    c2h_deposit_amount = get_balance(c2h_deposit_address, connection["asset"])
    unnotified_commit = db.unnotified_commit(
        channel_id=connection["h2c_channel_id"], cursor=cursor
    )
    h2c_payments_sum = db.h2c_payments_sum(handle=handle, cursor=cursor)
    c2h_payments_sum = db.c2h_payments_sum(handle=handle, cursor=cursor)
    payments_sum = h2c_payments_sum - c2h_payments_sum

    # sendable (what this channel can send to another)
    balance = (
        c2h_deposit_amount + h2c_transferred - c2h_transferred - payments_sum
    )

    # receivable (what this channel can receive from another)
    receivable_potential = h2c_deposit_amount + c2h_transferred
    receivable_owed = (abs(payments_sum) if payments_sum < 0 else 0)
    receivable_amount = receivable_potential - receivable_owed

    return {
        "connection": connection,
        "h2c_state": h2c_state,
        "h2c_expired": is_expired(h2c_state, etc.expire_clearance),
        "h2c_transferred_amount": h2c_transferred,
        "h2c_payments_sum": h2c_payments_sum,
        "h2c_deposit_amount": h2c_deposit_amount,
        "h2c_transferrable_amount": h2c_deposit_amount - h2c_transferred,
        "c2h_state": c2h_state,
        "c2h_expired": is_expired(c2h_state, etc.expire_clearance),
        "c2h_transferred_amount": c2h_transferred,
        "c2h_payments_sum": c2h_payments_sum,
        "c2h_deposit_amount": c2h_deposit_amount,
        "c2h_transferrable_amount": c2h_deposit_amount - c2h_transferred,
        "payments_sum": payments_sum,
        "unnotified_commit": unnotified_commit,  # FIXME rename h2c_uno...
        "balance": balance,
        "receivable_amount": receivable_amount,
        "terms": terms,
    }


def _send_client_funds(connection_data, quantity, token):

    c2h_state = connection_data["c2h_state"]
    h2c_state = connection_data["h2c_state"]

    handle = connection_data["connection"]["handle"]
    result = db.get_next_revoke_secret_hash(handle=handle)
    next_revoke_secret_hash = result["next_revoke_secret_hash"]
    deposit_script_bin = h2c_state["deposit_script"]
    hub_pubkey = scripts.get_deposit_payer_pubkey(deposit_script_bin)
    wif = db.key(pubkey=hub_pubkey)["wif"]

    def get_secret_func(h):
        return db.get_secret(hash=h)["value"]

    result = usr.MpcClient().full_duplex_transfer(
        wif, get_secret_func, h2c_state, c2h_state, quantity,
        next_revoke_secret_hash, etc.delay_time
    )

    return {
        "c2h_revoke_secrets": result["revokes"],
        "h2c_unnotified_commit": result["commit"],
        "h2c_state": result["send_state"],
        "c2h_state": result["recv_state"]
    }


def process_payment(payer_handle, cursor, payment):

    # load payer
    payer = load_connection_data(payer_handle, cursor)

    # check if connection expired
    if payer["c2h_expired"]:
        raise err.DepositExpired(payer_handle, "client")
    if payer["h2c_expired"]:
        raise err.DepositExpired(payer_handle, "hub")

    # check payer has enough funds or can revoke sends until enough available
    if payment["amount"] > payer["balance"]:
        raise err.PaymentExceedsSpendable(
            payment["amount"], payer["balance"], payment["token"]
        )

    # load payee
    payee_handle = payment["payee_handle"]
    if payee_handle:
        payee = load_connection_data(payee_handle, cursor)
        if payer["connection"]["asset"] != payee["connection"]["asset"]:
            raise err.AssetMissmatch(
                payer["connection"]["asset"], payee["connection"]["asset"]
            )

        # check if connection expired
        if payee["h2c_expired"]:
            raise err.DepositExpired(payee_handle, "hub")
        if payee["c2h_expired"]:
            raise err.DepositExpired(payee_handle, "client")

        if payment["amount"] > payee["receivable_amount"]:
            raise err.PaymentExceedsReceivable(
                payment["amount"], payee["receivable_amount"], payment["token"]
            )

        c2h_unnotified_revokes = db.unnotified_revokes(
            channel_id=payee["connection"]["c2h_channel_id"]
        )
        result = _send_client_funds(payee, payment["amount"], payment["token"])

        cursor.execute("BEGIN TRANSACTION;")

        c2h_unnotified_revokes += result["c2h_revoke_secrets"]
        db.save_channel_state(
            payee["connection"]["c2h_channel_id"], result["c2h_state"],
            unnotified_revoke_secrets=c2h_unnotified_revokes, cursor=cursor
        )
        db.save_channel_state(
            payee["connection"]["h2c_channel_id"], result["h2c_state"],
            unnotified_commit=result["h2c_unnotified_commit"], cursor=cursor
        )

    # fee payment
    else:
        cursor.execute("BEGIN TRANSACTION;")

    payment["payer_handle"] = payer_handle
    db.add_payment(cursor=cursor, **payment)
    cursor.execute("COMMIT;")


def terms(assets=None):

    # create terms and return default value
    if not os.path.exists(etc.path_terms):
        default_terms = TERMS["TESTNET"] if etc.testnet else TERMS["MAINNET"]
        with open(etc.path_terms, 'w') as outfile:
            json.dump(default_terms, outfile, indent=2)
        terms_data = copy.deepcopy(default_terms)

    # read terms
    else:
        with open(etc.path_terms, 'r') as infile:
            terms_data = json.load(infile)

    # FIXME validate terms data

    # limit to given assets
    if assets:
        for key in list(terms_data.keys())[:]:
            if key not in assets:
                terms_data.pop(key)

    return terms_data


def hub_connections(handles, assets):
    connections = []
    for connection in db.hub_connections():
        if assets is not None and connection["asset"] not in assets:
            continue
        if handles is not None and connection["handle"] not in handles:
            continue
        wif = connection.pop("wif")
        connection = auth.sign_json(connection, wif)
        connections.append(connection)
    return connections
