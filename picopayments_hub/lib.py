# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import copy
import json
import pkg_resources
import cachetools
from collections import defaultdict
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import b2h
from micropayment_core import util
from micropayment_core import keys
from micropayment_core import scripts
from counterpartylib.lib.util import DictCache
from picopayments_cli.mpc import Mpc
from picopayments_hub import db
from picopayments_hub import err
from picopayments_hub import etc
from picopayments_hub import sql


_TERMS_FP = pkg_resources.resource_stream("picopayments_hub", "terms.json")
TERMS = json.loads(_TERMS_FP.read().decode("utf-8"))


_LOCKS = DictCache(size=65535)  # address -> lock
_LOCKS_TTL = 3.0  # seconds
_LOCKS_MAX = 5000  # per address


def get_secret(secret_hash, cursor=None):
    result = db.get_secret(hash=secret_hash, cursor=cursor)
    if result:
        return result["value"]
    return None


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
    current_terms = get_terms().get(asset)
    data.update(current_terms)

    # new hub key
    hub_key = create_key(asset, netcode=etc.netcode)
    data["hub_wif"] = hub_key["wif"]
    data["hub_pubkey"] = hub_key["pubkey"]
    data["hub_address"] = hub_key["address"]

    # client key
    data["client_pubkey"] = client_pubkey
    data["client_address"] = keys.address_from_pubkey(client_pubkey,
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
        "c2h_deposit_address": util.script_address(
            c2h_deposit_script, netcode=etc.netcode
        ),
        "h2c_channel_id": hub_conn["h2c_channel_id"],
        "h2c_deposit_script": h2c_deposit_script,
        "h2c_deposit_address": util.script_address(
            h2c_deposit_script, netcode=etc.netcode
        ),
        "next_revoke_secret_hash": next_revoke_secret_hash,
    }

    data.update(create_secret())  # revoke secret

    db.complete_hub_connection(data)
    return (
        {
            "deposit_script": h2c_deposit_script,
            "next_revoke_secret_hash": data["secret_hash"]
        },
        hub_key["wif"]
    )


def find_key_with_funds(asset, asset_quantity, btc_quantity):
    nearest = {"key": None, "available": 2100000000000000}
    for key in db.keys(asset=asset):
        address = key["address"]
        # FIXME ignore if locked by counterpartylib
        if has_unconfirmed_transactions(address):
            continue  # ignore if unconfirmed inputs/outputs
        if key["address"] in _LOCKS:
            continue  # ignore recently used to avoid doublespends
        balances = get_balances(address, assets=["BTC", asset])
        if btc_quantity > balances["BTC"]:
            continue  # not enough btc
        if asset_quantity > balances[asset]:
            continue  # not enough assets
        if nearest["available"] > balances[asset]:
            nearest = {"key": key, "available": balances[asset]}
    return nearest["key"]


def get_funding_addresses(assets=None):
    assets = _terms_assets(assets=assets)
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

    get_terms()  # make sure terms file exists
    db.setup()  # setup and create db if needed


def update_channel_state(channel_id, asset, commit=None,
                         revokes=None, cursor=None):
    from picopayments_hub import api

    state = db.load_channel_state(channel_id, asset, cursor=cursor)
    unnotified_revokes = db.unnotified_revokes(channel_id=channel_id)
    unnotified_commit = db.unnotified_commit(channel_id=channel_id,
                                             cursor=cursor)
    unnotified_revoke_secrets = [x["revoke_secret"]
                                 for x in unnotified_revokes]
    if commit is not None:
        state = api.mpc_add_commit(
            state=state,
            commit_rawtx=commit["rawtx"],
            commit_script=commit["script"]
        )
    if revokes is not None:
        # FIXME will not set revokes as unnotified
        #       currently not a problem as its only used for hub to client
        #       but its begging to be missused!!
        state = api.mpc_revoke_all(state=state, secrets=revokes)
    cursor.execute("BEGIN TRANSACTION;")
    db.save_channel_state(
        channel_id, state, h2c_unnotified_commit=unnotified_commit,
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
    if h2c_revokes:
        db.set_revokes_notified(h2c_revokes, cursor=cursor)

    # save next spend secret
    db.add_revoke_secret(c2h_id, next_revoke_secret["secret_hash"],
                         next_revoke_secret["secret_value"], cursor=cursor)

    cursor.execute("COMMIT;")


def recover_funds(hub_connection, cursor=None):
    from picopayments_hub import api
    asset = hub_connection["asset"]
    c2h_mpc_id = hub_connection["c2h_channel_id"]
    h2c_mpc_id = hub_connection["h2c_channel_id"]
    c2h_state = db.load_channel_state(c2h_mpc_id, asset, cursor=cursor)
    h2c_state = db.load_channel_state(h2c_mpc_id, asset, cursor=cursor)
    txs = Mpc(api).full_duplex_recover_funds(
        get_wif, get_secret, c2h_state, h2c_state
    )
    return txs


def close_connection(handle, h2c_spend_secret=None):

    cursor = sql.get_cursor()
    hub_connection = db.hub_connection(handle=handle, cursor=cursor)

    # save secret if given and not already known
    if h2c_spend_secret is not None:
        secret_hash = util.hash160hex(h2c_spend_secret)
        if not get_secret(secret_hash):
            db.add_secret(secret_value=h2c_spend_secret,
                          secret_hash=secret_hash, cursor=cursor)

    # close connection if not already done
    if not hub_connection["closed"]:
        db.set_connection_closed(handle=handle, cursor=cursor)

    # get c2h spend secret if no commits for channel
    c2h_spend_secret = None
    c2h_state = db.load_channel_state(hub_connection["c2h_channel_id"],
                                      hub_connection["asset"], cursor=cursor)
    if len(c2h_state["commits_active"]) == 0:
        c2h_spend_secret_hash = scripts.get_deposit_spend_secret_hash(
            c2h_state["deposit_script"]
        )
        c2h_spend_secret = get_secret(c2h_spend_secret_hash)

    hub_key = db.channel_payer_key(id=hub_connection["h2c_channel_id"])
    return ({"spend_secret": c2h_spend_secret}, hub_key["wif"])


def sync_hub_connection(handle, next_revoke_secret_hash,
                        payments, commit, revokes):

    cursor = sql.get_cursor()
    hub_connection = db.hub_connection(handle=handle, cursor=cursor)

    _update_channel_state(hub_connection, commit, revokes, cursor)
    _process_payments(handle, payments, hub_connection, cursor)
    _balance_channel(handle, cursor)
    next_revoke_secret = create_secret()  # create next spend secret

    # load unnotified
    c2h_id = hub_connection["c2h_channel_id"]
    h2c_id = hub_connection["h2c_channel_id"]
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


def _terms_assets(assets=None):
    """limit to terms assets and use all terms assets if none given"""
    if assets is not None:
        return set(get_terms().keys()).intersection(set(assets))
    return get_terms().keys()


def get_hub_liquidity(assets=None):
    assets = _terms_assets(assets=assets)

    result = {
        "total": defaultdict(lambda: 0),
        "addresses": defaultdict(lambda: []),
    }

    for asset in assets:
        for key in db.keys(asset=asset):

            # get balance for asset address
            balances = get_balances(
                key["address"], assets=["BTC", key["asset"]]
            )

            # do not show keys with no balances
            if not sum(balances.values()):
                continue

            # update total
            for asset, quantity in balances.items():
                result["total"][asset] += quantity

            # add balance to addresses
            result["addresses"][key["asset"]].append({
                "address": key["address"],
                "balances": balances
            })
    return result


def get_balances(address, assets=None):
    from picopayments_hub import api
    return Mpc(api).get_balances(address=address, assets=assets)


def get_connections_status(assets=None):
    # FIXME limit to only open connections
    # FIXME limit by asset
    connections = {}
    for hub_conn in db.hub_connections_open():
        connections[hub_conn["handle"]] = get_status(hub_conn)
    return connections


def get_status(hub_conn, clearance=6, cursor=None):
    from picopayments_hub import api

    send_state = db.load_channel_state(
        hub_conn["h2c_channel_id"], hub_conn["asset"], cursor=cursor
    )
    recv_state = db.load_channel_state(
        hub_conn["c2h_channel_id"], hub_conn["asset"], cursor=cursor
    )
    status = Mpc(api).full_duplex_channel_status(
        hub_conn["handle"], etc.netcode, send_state,
        recv_state, get_secret, clearance=clearance
    )
    return {
        "asset": status["asset"],
        "balance": status["balance"],
        "ttl": status["ttl"],
        "status": status["status"]
    }


def deposit_address(state):
    return get_script_address(state["deposit_script"])


def get_script_address(script):
    return util.script_address(script, netcode=etc.netcode)


def get_transferred_quantity(state):
    from picopayments_hub import api
    return api.mpc_transferred_amount(state=state)


def is_expired(state, clearance):
    from picopayments_hub import api
    return api.mpc_deposit_ttl(state=state, clearance=clearance) == 0


def get_tx(txid):
    from picopayments_hub import api
    return api.getrawtransaction(tx_hash=txid)


def publish(rawtx):
    from picopayments_hub import api
    return api.sendrawtransaction(tx_hex=rawtx)  # pragma: no cover


def send_funds(destination, asset, quantity):
    from picopayments_hub import api
    regular_dust_size = 5500  # FIXME get from cplib
    fee_per_kb = 25000  # FIXME get from cplib
    fee = int(fee_per_kb / 2)
    extra_btc = (fee + regular_dust_size) * 3
    key = find_key_with_funds(asset, quantity, extra_btc)
    if key is None:
        raise err.InsufficientFunds(asset, quantity)
    unsigned_rawtx = api.create_send(
        source=key["address"],
        destination=destination,
        asset=asset,
        regular_dust_size=extra_btc,
        quantity=quantity,
    )
    _LOCKS[key["address"]] = cachetools.TTLCache(_LOCKS_MAX, _LOCKS_TTL)
    signed_rawtx = scripts.sign_deposit(get_tx, key["wif"], unsigned_rawtx)
    return publish(signed_rawtx)


def get_transactions(address):
    from picopayments_hub import api
    return api.search_raw_transactions(address=address, unconfirmed=True)


def has_unconfirmed_transactions(address):
    transactions = get_transactions(address)
    for transaction in transactions:
        if transaction.get("confirmations", 0) == 0:
            return True
    return False


def load_connection_data(handle, cursor):

    # connection data
    connection = db.hub_connection(handle=handle, cursor=cursor)
    asset = connection["asset"]
    terms = db.terms(id=connection["terms_id"], cursor=cursor)

    # h2c data
    h2c_state = db.load_channel_state(
        connection["h2c_channel_id"], connection["asset"], cursor=cursor
    )
    h2c_deposit_address = deposit_address(h2c_state)
    h2c_transferred = get_transferred_quantity(h2c_state)
    h2c_deposit = get_balances(h2c_deposit_address, [asset])[asset]
    h2c_unnotified_commit = db.unnotified_commit(
        channel_id=connection["h2c_channel_id"], cursor=cursor
    )

    # c2h data
    c2h_state = db.load_channel_state(
        connection["c2h_channel_id"], connection["asset"], cursor=cursor
    )
    c2h_transferred = get_transferred_quantity(c2h_state)

    # payments
    send_payments_sum = db.send_payments_sum(handle=handle, cursor=cursor)
    recv_payments_sum = db.recv_payments_sum(handle=handle, cursor=cursor)
    payments_sum = recv_payments_sum - send_payments_sum

    # sendable (what this channel can send to another)
    sendable_amount = c2h_transferred + payments_sum - h2c_transferred
    assert sendable_amount >= 0

    # receivable (what this channel can receive from another)
    receivable_amount = h2c_deposit + c2h_transferred - payments_sum
    assert receivable_amount >= 0

    return {
        "connection": connection,
        "h2c_state": h2c_state,
        "h2c_expired": is_expired(h2c_state, etc.expire_clearance),
        "c2h_state": c2h_state,
        "c2h_expired": is_expired(c2h_state, etc.expire_clearance),
        "h2c_unnotified_commit": h2c_unnotified_commit,  # FIXME remove
        "sendable_amount": sendable_amount,
        "receivable_amount": receivable_amount,
        "terms": terms,
    }


def _send_client_funds(connection_data, quantity):
    from picopayments_hub import api

    c2h_state = connection_data["c2h_state"]
    h2c_state = connection_data["h2c_state"]

    handle = connection_data["connection"]["handle"]
    result = db.get_next_revoke_secret_hash(handle=handle)
    next_revoke_secret_hash = result["next_revoke_secret_hash"]
    deposit_script_bin = h2c_state["deposit_script"]
    hub_pubkey = scripts.get_deposit_payer_pubkey(deposit_script_bin)
    wif = db.key(pubkey=hub_pubkey)["wif"]

    result = Mpc(api).full_duplex_transfer(
        wif, get_secret, h2c_state, c2h_state, quantity,
        next_revoke_secret_hash, etc.delay_time
    )

    return {
        "c2h_revoke_secrets": result["revokes"],
        "h2c_unnotified_commit": result["commit"],
        "h2c_state": result["send_state"],
        "c2h_state": result["recv_state"]
    }


def _check_payment_payer(payer, payment, payer_handle):
    if payer["c2h_expired"]:
        raise err.DepositExpired(payer_handle, "client")
    if payer["h2c_expired"]:
        raise err.DepositExpired(payer_handle, "hub")
    if payment["amount"] > payer["sendable_amount"]:
        raise err.PaymentExceedsSpendable(
            payment["amount"], payer["sendable_amount"], payment["token"]
        )


def _check_payment_payee(payer, payee, payment, payee_handle):
    if payer["connection"]["asset"] != payee["connection"]["asset"]:
        raise err.AssetMissmatch(
            payer["connection"]["asset"], payee["connection"]["asset"]
        )
    if payee["h2c_expired"]:
        raise err.DepositExpired(payee_handle, "hub")
    if payee["c2h_expired"]:
        raise err.DepositExpired(payee_handle, "client")
    if payment["amount"] > payee["receivable_amount"]:
        raise err.PaymentExceedsReceivable(
            payment["amount"], payee["receivable_amount"], payment["token"]
        )


def _update_channel_state(hub_connection, commit, revokes, cursor):
    asset = hub_connection["asset"]
    c2h_id = hub_connection["c2h_channel_id"]
    h2c_id = hub_connection["h2c_channel_id"]
    update_channel_state(c2h_id, asset, commit=commit, cursor=cursor)
    update_channel_state(h2c_id, asset, revokes=revokes, cursor=cursor)


def _process_payments(payer_handle, payments, hub_connection, cursor):

    connection_terms = db.terms(id=hub_connection["terms_id"])

    # add sync fee payment
    payments.insert(0, {
        "payee_handle": None,  # to hub
        "amount": connection_terms["sync_fee"],
        "token": "sync_fee"
    })

    # process payments
    for payment in payments:

        # check payer
        payer = load_connection_data(payer_handle, cursor)
        _check_payment_payer(payer, payment, payer_handle)

        # check payee
        payee_handle = payment["payee_handle"]
        if payee_handle:
            payee = load_connection_data(payee_handle, cursor)
            _check_payment_payee(payer, payee, payment, payee_handle)

        payment["payer_handle"] = payer_handle
        db.add_payment(cursor=cursor, **payment)


def _balance_channel(handle, cursor):
    connection_data = load_connection_data(handle, cursor)

    c2h_unnotified_revokes = db.unnotified_revokes(
        channel_id=connection_data["connection"]["c2h_channel_id"]
    )
    prev_unnotified_commit = connection_data["h2c_unnotified_commit"]
    quantity = connection_data["sendable_amount"]
    result = _send_client_funds(connection_data, quantity)

    # remove previously unnotified commit if never sent to client
    # required avoid commit transactions sharing secrets
    h2c_commits_active = result["h2c_state"]["commits_active"]
    prev_h2c_commits_active = connection_data["h2c_state"]["commits_active"]
    new_commit = len(h2c_commits_active) != len(prev_h2c_commits_active)
    if prev_unnotified_commit is not None and new_commit:
        del h2c_commits_active[-2]  # unnotified is always second highest

    cursor.execute("BEGIN TRANSACTION;")
    c2h_unnotified_revokes += result["c2h_revoke_secrets"]
    db.save_channel_state(
        connection_data["connection"]["c2h_channel_id"], result["c2h_state"],
        unnotified_revoke_secrets=c2h_unnotified_revokes, cursor=cursor
    )
    db.save_channel_state(
        connection_data["connection"]["h2c_channel_id"], result["h2c_state"],
        h2c_unnotified_commit=result["h2c_unnotified_commit"], cursor=cursor
    )
    cursor.execute("COMMIT;")


def get_terms(assets=None):

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
