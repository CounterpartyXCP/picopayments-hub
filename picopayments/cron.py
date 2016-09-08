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
        txids = []
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
                txids.append(txid)

        return txids


def close_connections():
    """Close connections almost expired and partially closed by client."""
    with etc.database_lock:
        pass


def recover_funds():
    """Recover funds where possible"""
    with etc.database_lock:
        pass


def collect_garbage():
    """Remove database entries no longer needed."""
    with etc.database_lock:
        pass


def run():
    with etc.database_lock:
        close_connections()
        recover_funds()
        collect_garbage()
        fund_deposits()
