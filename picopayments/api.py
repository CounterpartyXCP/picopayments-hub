# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


from jsonrpc import dispatcher
from picopayments import db
from picopayments import auth
from picopayments import validate
from picopayments import ctrl
from picopayments import rpc


@dispatcher.add_method
def mpc_hub_terms(assets=None):
    validate.terms_input(assets)
    return ctrl.terms(assets=assets)


@dispatcher.add_method
def mpc_hub_connections(handles=None, assets=None):
    validate.connections_input(handles, assets)
    return ctrl.hub_connections(handles, assets)


@dispatcher.add_method
def mpc_hub_request(**kwargs):
    with db.lock:
        auth.verify_json(kwargs)
        validate.request_input(
            kwargs["asset"],
            kwargs["pubkey"],
            kwargs["spend_secret_hash"],
            kwargs.get("hub_rpc_url")
        )
        result, authwif = ctrl.create_hub_connection(
            kwargs["asset"],
            kwargs["pubkey"],
            kwargs["spend_secret_hash"],
            kwargs.get("hub_rpc_url")
        )
        return auth.sign_json(result, authwif)


@dispatcher.add_method
def mpc_hub_deposit(**kwargs):
    with db.lock:
        auth.verify_json(kwargs)
        validate.deposit_input(
            kwargs["handle"],
            kwargs["deposit_script"],
            kwargs["next_revoke_secret_hash"],
            kwargs["pubkey"]
        )
        result, authwif = ctrl.complete_connection(
            kwargs["handle"],
            kwargs["deposit_script"],
            kwargs["next_revoke_secret_hash"]
        )
        return auth.sign_json(result, authwif)


@dispatcher.add_method
def mpc_hub_sync(**kwargs):
    with db.lock:
        auth.verify_json(kwargs)
        validate.sync_input(
            kwargs["handle"],
            kwargs["next_revoke_secret_hash"],
            kwargs["pubkey"],
            kwargs.get("sends"),
            kwargs.get("commit"),
            kwargs.get("revokes")
        )
        result, authwif = ctrl.sync_hub_connection(
            kwargs["handle"],
            kwargs["next_revoke_secret_hash"],
            kwargs.get("sends"),
            kwargs.get("commit"),
            kwargs.get("revokes")
        )
        return auth.sign_json(result, authwif)


def _add_cp_call(method):
    def counterparty_method(**kwargs):
        return rpc.cp_call(method=method, params=kwargs)
    dispatcher[method] = counterparty_method
    return counterparty_method


getrawtransaction = _add_cp_call("getrawtransaction")
get_unspent_txouts = _add_cp_call("get_unspent_txouts")
create_send = _add_cp_call("create_send")
sendrawtransaction = _add_cp_call("sendrawtransaction")
mpc_make_deposit = _add_cp_call("mpc_make_deposit")
mpc_set_deposit = _add_cp_call("mpc_set_deposit")
mpc_request_commit = _add_cp_call("mpc_request_commit")
mpc_create_commit = _add_cp_call("mpc_create_commit")
mpc_add_commit = _add_cp_call("mpc_add_commit")
mpc_revoke_hashes_until = _add_cp_call("mpc_revoke_hashes_until")
mpc_revoke_all = _add_cp_call("mpc_revoke_all")
mpc_heighest_commit = _add_cp_call("mpc_heighest_commit")
mpc_transferred_amount = _add_cp_call("mpc_transferred_amount")
mpc_payouts = _add_cp_call("mpc_payouts")
mpc_recoverables = _add_cp_call("mpc_recoverables")
mpc_recoverables = _add_cp_call("mpc_deposit_expired")
