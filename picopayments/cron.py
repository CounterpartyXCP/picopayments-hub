# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


from picopayments import etc
from picopayments import db
from picopayments import lib
from picopayments import sql
from picopayments import rpc
from counterpartylib.lib.micropayments import util


def fund_deposits(publish_tx=True):
    """Fund or top off open channels."""
    with etc.database_lock:
        deposits = []
        cursor = sql.get_cursor()
        for hub_connection in db.hub_connections_complete(cursor=cursor):

            asset = hub_connection["asset"]
            terms = db.terms(id=hub_connection["terms_id"], cursor=cursor)

            # load client to hub data
            c2h_mpc_id = hub_connection["client2hub_channel_id"]
            c2h_state = db.load_channel_state(c2h_mpc_id, asset, cursor=cursor)
            c2h_deposit_address = lib.deposit_address(c2h_state)
            c2h_deposit_balance = lib.balance(c2h_deposit_address, asset)

            if c2h_deposit_balance < terms["deposit_min"]:
                continue  # ignore if client deposit insufficient
            if lib.expired(c2h_state, etc.fund_clearance):
                continue  # ignore if expires soon
            if lib.has_unconfirmed_transactions(c2h_deposit_address):
                continue  # ignore if unconfirmed transaction inputs/outputs

            # load hub to client data
            h2c_mpc_id = hub_connection["hub2client_channel_id"]
            h2c_state = db.load_channel_state(h2c_mpc_id, asset, cursor=cursor)
            h2c_deposit_address = lib.deposit_address(h2c_state)
            h2c_deposit_balance = lib.balance(h2c_deposit_address, asset)

            if lib.expired(h2c_state, etc.fund_clearance):
                continue  # ignore if expires soon
            if lib.has_unconfirmed_transactions(h2c_deposit_address):
                continue  # ignore if unconfirmed transaction inputs/outputs

            # fund hub to client if needed
            deposit_max = terms["deposit_max"]
            deposit_ratio = terms["deposit_ratio"]
            if deposit_max:
                target = min(deposit_max, c2h_deposit_balance) * deposit_ratio
            else:
                target = int(c2h_deposit_balance * deposit_ratio)
            quantity = target - h2c_deposit_balance
            if quantity > 0:
                txid = lib.send(h2c_deposit_address, asset,
                                quantity, publish_tx=publish_tx)
                deposits.append({
                    "txid": txid,
                    "asset": asset,
                    "address": h2c_deposit_address,
                    "quantity": quantity,
                    "handle": hub_connection["handle"]
                })

        return deposits


def close_connections(publish_tx=True):
    """Close connections almost expired and partially closed by client."""
    with etc.database_lock:
        closed_connections = []
        cursor = sql.get_cursor()
        for hub_connection in db.hub_connections_complete(cursor=cursor):
            asset = hub_connection["asset"]
            c2h_mpc_id = hub_connection["client2hub_channel_id"]
            c2h_state = db.load_channel_state(c2h_mpc_id, asset, cursor=cursor)
            h2c_mpc_id = hub_connection["hub2client_channel_id"]
            h2c_state = db.load_channel_state(h2c_mpc_id, asset, cursor=cursor)

            # connection expired or  commit published
            c2h_expired = lib.expired(c2h_state, etc.fund_clearance)
            h2c_expired = lib.expired(h2c_state, etc.fund_clearance)
            if c2h_expired or h2c_expired or lib.commit_published(h2c_state):
                db.set_connection_closed(handle=hub_connection["handle"])
                commit_txid = lib.publish_highest_commit(
                    c2h_state, publish_tx=publish_tx
                )
                closed_connections.append({
                    "handle": hub_connection["handle"],
                    "commit_txid": commit_txid
                })
                continue

        return closed_connections


def recover_funds(publish_tx=True):
    """Recover funds where possible"""
    with etc.database_lock:
        pass


def collect_garbage():
    """Remove database entries no longer needed."""
    with etc.database_lock:
        pass


def run(publish_tx=True):
    with etc.database_lock:
        close_connections(publish_tx=publish_tx)
        recover_funds(publish_tx=publish_tx)
        fund_deposits(publish_tx=publish_tx)
        collect_garbage()
