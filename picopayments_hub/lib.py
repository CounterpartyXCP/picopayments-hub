# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import copy
import json
import pkg_resources
import cachetools
from micropayment_core import util
from micropayment_core import keys
from micropayment_core import scripts
from counterpartylib.lib.util import DictCache
from picopayments_cli.mpc import Mpc
from picopayments_cli.auth import load_wif
from picopayments_hub import db
from picopayments_hub import err
from picopayments_hub import etc
from picopayments_hub import sql


_TERMS_FP = pkg_resources.resource_stream("picopayments_hub", "terms.json")
TERMS = json.loads(_TERMS_FP.read().decode("utf-8"))

_UTXO_LOCKS = DictCache(size=65535)  # "utxo_txid:utxo_index" -> lock
_UTXO_LOCKS_TTL = 3.0  # seconds
_UTXO_LOCKS_MAX = 5000  # per address


def get_secret(secret_hash, cursor=None):
    result = db.get_secret(hash=secret_hash, cursor=cursor)
    if result:
        return result["value"]
    return None


def get_wif(pubkey):
    wif = load_wif()
    assert(pubkey == keys.pubkey_from_wif(wif))
    return wif


def get_funding_address():
    return keys.address_from_wif(load_wif())


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
    hub_wif = load_wif()
    data["hub_pubkey"] = keys.pubkey_from_wif(hub_wif)
    data["hub_address"] = keys.address_from_wif(hub_wif)

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
        hub_wif
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

    hub_wif = get_wif(hub_pubkey)

    return hub_conn, h2c, expire_time, hub_wif


def complete_connection(handle, c2h_deposit_script,
                        next_revoke_secret_hash):

    hub_conn, h2c, expire_time, hub_wif = _load_incomplete_connection(
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
        hub_wif
    )


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
        # TODO will not set revokes as unnotified
        #      currently not a problem as its only used for hub to client
        #      but its begging to be missused!!
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
    return Mpc(api).full_duplex_recover_funds(
        get_wif, get_secret, c2h_state, h2c_state
    )


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

    hub_wif = load_wif()
    return ({"spend_secret": c2h_spend_secret}, hub_wif)


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

    hub_wif = load_wif()
    return (
        {
            "receive": receive_payments,
            "commit": h2c_commit,
            "revokes": [r["revoke_secret"] for r in c2h_revokes],
            "next_revoke_secret_hash": next_revoke_secret["secret_hash"]
        },
        hub_wif
    )


def _terms_assets(assets=None):
    """limit to terms assets and use all terms assets if none given"""
    if assets is not None:
        return set(get_terms().keys()).intersection(set(assets))
    return get_terms().keys()


def get_hub_liquidity(assets=None):
    assets = _terms_assets(assets=assets)
    # TODO sign something known to prove control of address
    address = keys.address_from_wif(load_wif())
    return get_balances(address, assets=assets)


def get_balances(address, assets=None):
    from picopayments_hub import api
    return Mpc(api).get_balances(address=address, assets=assets)


def get_connections_status(assets=None):
    connections = {}
    for hub_conn in db.hub_connections_open():
        if assets is not None and hub_conn["asset"] not in assets:
            continue
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


def get_txs(txids):
    from picopayments_hub import api
    return api.getrawtransaction_batch(txhash_list=txids)


def publish(rawtx):
    from picopayments_hub import api
    return api.sendrawtransaction(tx_hex=rawtx)  # pragma: no cover


def send_funds(destination, asset, quantity):
    from picopayments_hub import api
    regular_dust_size = 5500  # TODO get from cplib
    fee_per_kb = 25000  # TODO get from cplib
    fee = int(fee_per_kb / 2)
    extra_btc = (fee + regular_dust_size) * 3
    wif = load_wif()
    address = keys.address_from_wif(wif)
    utxos = _get_hub_utxos(address, asset, quantity, extra_btc)
    unsigned_rawtx = api.create_send(
        source=address,
        destination=destination,
        asset=asset,
        regular_dust_size=extra_btc,
        quantity=quantity,
        disable_utxo_locks=True,
        custom_inputs=utxos,
    )
    signed_rawtx = scripts.sign_deposit(get_txs, wif, unsigned_rawtx)
    return publish(signed_rawtx)


def _getutxoid(utxo):
    return "{0}:{1}".format(utxo["txid"], utxo["vout"])


def _get_hub_utxos(address, asset, asset_quantity, btc_quantity):
    from picopayments_hub import api

    # FIXME includes unconfirmed spends but not deposits!
    asset_balance = get_balances(address, assets=[asset])[asset]
    if asset_balance < asset_quantity:
        raise err.InsufficientFunds(asset, asset_quantity)

    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    utxo_sum = 0
    results = []
    for utxo in utxos:
        utxoid = _getutxoid(utxo)
        if utxoid in _UTXO_LOCKS:
            continue
        if utxo_sum >= btc_quantity:
            break
        utxo_sum += util.to_satoshis(utxo["amount"])
        _UTXO_LOCKS[utxoid] = cachetools.TTLCache(
            _UTXO_LOCKS_MAX, _UTXO_LOCKS_TTL
        )
        results.append(utxo)
    if utxo_sum < btc_quantity:
        raise err.InsufficientFunds("BTC", btc_quantity)

    return results


def get_transactions(address):
    from picopayments_hub import api
    return api.search_raw_transactions(address=address, unconfirmed=True)


def has_unconfirmed_transactions(address):
    transactions = get_transactions(address)
    for transaction in transactions:
        if transaction.get("confirmations", 0) == 0:
            return True
    return False


def load_connection_data(handle, new_c2h_commit=None,
                         new_h2c_revokes=None, cursor=None):
    from picopayments_hub import api
    # TODO this is getting dangerous, used in lib and verify, split it up!

    # connection data
    connection = db.hub_connection(handle=handle, cursor=cursor)
    if not connection:
        raise err.HandleNotFound(handle)
    asset = connection["asset"]
    terms = db.terms(id=connection["terms_id"], cursor=cursor)

    # h2c data
    h2c_state = db.load_channel_state(
        connection["h2c_channel_id"], connection["asset"], cursor=cursor
    )
    if new_h2c_revokes is not None:
        h2c_state = api.mpc_revoke_all(state=h2c_state,
                                       secrets=new_h2c_revokes)
    h2c_deposit_address = deposit_address(h2c_state)
    h2c_transferred = get_transferred_quantity(h2c_state)
    h2c_deposit = get_balances(h2c_deposit_address, [asset])[asset]

    # TODO remove now impossable unnotified commit?
    h2c_unnotified_commit = db.unnotified_commit(
        channel_id=connection["h2c_channel_id"], cursor=cursor
    )

    # c2h data
    c2h_state = db.load_channel_state(
        connection["c2h_channel_id"], connection["asset"], cursor=cursor
    )
    if new_c2h_commit is not None:
        c2h_state = api.mpc_add_commit(
            state=c2h_state,
            commit_rawtx=new_c2h_commit["rawtx"],
            commit_script=new_c2h_commit["script"]
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
        "h2c_unnotified_commit": h2c_unnotified_commit,
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
    wif = get_wif(hub_pubkey)

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


def _update_channel_state(hub_connection, commit, revokes, cursor):
    asset = hub_connection["asset"]
    c2h_id = hub_connection["c2h_channel_id"]
    h2c_id = hub_connection["h2c_channel_id"]
    update_channel_state(c2h_id, asset, commit=commit, cursor=cursor)
    update_channel_state(h2c_id, asset, revokes=revokes, cursor=cursor)


def _process_payments(payer_handle, payments, hub_connection, cursor):

    # add sync fee payment
    connection_terms = db.terms(id=hub_connection["terms_id"])
    payments.insert(0, {
        "payee_handle": None,  # to hub
        "amount": connection_terms["sync_fee"],
        "token": "sync_fee"
    })

    # process payments
    for payment in payments:
        payment["payer_handle"] = payer_handle
        db.add_payment(cursor=cursor, **payment)


def _balance_channel(handle, cursor):
    connection_data = load_connection_data(handle, cursor=cursor)

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

    # TODO validate terms data

    # limit to given assets
    if assets:
        for key in list(terms_data.keys())[:]:
            if key not in assets:
                terms_data.pop(key)

    return terms_data
