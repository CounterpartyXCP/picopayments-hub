# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import time
from picopayments_hub import etc
from picopayments_hub import db
from picopayments_hub import lib
from picopayments_hub import sql
from picopayments_hub import api
from micropayment_core import util
from micropayment_core.scripts import get_deposit_spend_secret_hash
from picopayments_cli.mpc import Mpc


# FIXME use http interface to ensure its called in the same process


def fund_deposits():
    """Fund or top off open channels."""
    with etc.database_lock:
        deposits = []
        cursor = sql.get_cursor()
        for hub_connection in db.hub_connections_open(cursor=cursor):

            asset = hub_connection["asset"]
            terms = db.terms(id=hub_connection["terms_id"], cursor=cursor)

            # load client to hub data
            c2h_mpc_id = hub_connection["c2h_channel_id"]
            c2h_state = db.load_channel_state(c2h_mpc_id, asset, cursor=cursor)
            c2h_deposit_address = lib.deposit_address(c2h_state)
            c2h_deposit_balance = lib.get_balances(c2h_deposit_address,
                                                   assets=[asset])[asset]

            if c2h_deposit_balance < terms["deposit_min"]:
                continue  # ignore if client deposit insufficient
            if lib.is_expired(c2h_state, etc.expire_clearance):
                continue  # ignore if expires soon
            if lib.has_unconfirmed_transactions(c2h_deposit_address):
                continue  # ignore if unconfirmed transaction inputs/outputs
            if api.mpc_published_commits(state=c2h_state):
                continue  # ignore if c2h commit published

            # load hub to client data
            h2c_mpc_id = hub_connection["h2c_channel_id"]
            h2c_state = db.load_channel_state(h2c_mpc_id, asset, cursor=cursor)
            h2c_deposit_address = lib.deposit_address(h2c_state)
            h2c_deposit_balance = lib.get_balances(h2c_deposit_address,
                                                   assets=[asset])[asset]

            if lib.is_expired(h2c_state, etc.expire_clearance):
                continue  # ignore if expires soon
            if lib.has_unconfirmed_transactions(h2c_deposit_address):
                continue  # ignore if unconfirmed transaction inputs/outputs
            if api.mpc_published_commits(state=h2c_state):
                continue  # ignore if h2c commit published

            # fund hub to client if needed
            deposit_max = terms["deposit_max"]
            deposit_ratio = terms["deposit_ratio"]
            if deposit_max:
                target = min(deposit_max, c2h_deposit_balance) * deposit_ratio
            else:
                target = int(c2h_deposit_balance * deposit_ratio)
            quantity = target - h2c_deposit_balance
            if quantity > 0:
                txid = lib.send_funds(h2c_deposit_address, asset, quantity)
                deposits.append({
                    "txid": txid,
                    "asset": asset,
                    "address": h2c_deposit_address,
                    "quantity": quantity,
                    "handle": hub_connection["handle"]
                })

        return deposits


def publish_commits():
    with etc.database_lock:
        commit_rawtxs = []
        cursor = sql.get_cursor()
        for hub_connection in db.hub_connections_complete(cursor=cursor):
            asset = hub_connection["asset"]
            c2h_mpc_id = hub_connection["c2h_channel_id"]
            c2h_state = db.load_channel_state(c2h_mpc_id, asset, cursor=cursor)
            h2c_mpc_id = hub_connection["h2c_channel_id"]
            h2c_state = db.load_channel_state(h2c_mpc_id, asset, cursor=cursor)
            h2c_spend_secret_hash = get_deposit_spend_secret_hash(
                h2c_state["deposit_script"]
            )
            h2c_spend_secret = lib.get_secret(h2c_spend_secret_hash)
            c2h_expired = lib.is_expired(c2h_state, etc.expire_clearance)
            h2c_expired = lib.is_expired(h2c_state, etc.expire_clearance)
            expired = c2h_expired or h2c_expired
            h2c_commits_published = api.mpc_published_commits(state=h2c_state)
            closed = hub_connection["closed"] != 0

            # connection expired or commit published or spend secret known
            if expired or closed or h2c_commits_published or h2c_spend_secret:
                if not closed:
                    db.set_connection_closed(handle=hub_connection["handle"])
                rawtx = Mpc(api).finalize_commit(lib.get_wif, c2h_state)
                if rawtx:
                    commit_rawtxs.append(rawtx)

        return commit_rawtxs


def _merge_rawtxs(a, b):
    merged = {
        "payout": {},
        "revoke": {},
        "change": {},
        "expire": {},
        "commit": {}
    }
    merged["payout"].update(a["payout"])
    merged["revoke"].update(a["revoke"])
    merged["change"].update(a["change"])
    merged["expire"].update(a["expire"])
    merged["commit"].update(a["commit"])
    merged["payout"].update(b["payout"])
    merged["revoke"].update(b["revoke"])
    merged["change"].update(b["change"])
    merged["expire"].update(b["expire"])
    merged["commit"].update(b["commit"])
    return merged


def recover_funds():
    """Recover funds where possible"""
    with etc.database_lock:
        rawtxs = {
            "payout": {},
            "revoke": {},
            "change": {},
            "expire": {},
            "commit": {}
        }
        cursor = sql.get_cursor()
        for hub_connection in db.hub_connections_recoverable(cursor=cursor):
            result = lib.recover_funds(hub_connection, cursor=cursor)
            rawtxs = _merge_rawtxs(rawtxs, result)
        return rawtxs


def collect_garbage():
    """Remove database entries no longer needed."""
    with etc.database_lock:
        pass


def run_all():
    with etc.database_lock:
        commit_rawtxs = publish_commits()
        rawtxs = recover_funds()
        for commit_rawtx in commit_rawtxs:
            rawtxs["commit"][util.gettxid(commit_rawtx)] = commit_rawtxs
        fund_deposits()  # FIXME add created rawtxs
        collect_garbage()
        print("RAWTXS:", time.time(), rawtxs)
        return rawtxs
