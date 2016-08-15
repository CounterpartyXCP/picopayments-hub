# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


from jsonrpc import dispatcher
from picopayments import db
from picopayments import auth
from picopayments import verify
from picopayments import ctrl
from picopayments import rpc


@dispatcher.add_method
def mpc_hub_terms(assets=None):
    all_trems = ctrl.terms()
    if assets:
        for key in list(all_trems.keys())[:]:
            if key not in assets:
                all_trems.pop(key)
    return all_trems


# @dispatcher.add_method
# def mpc_hub_clients(clients=None, assets=None):
#     # FIXME verify input
#     print("mpc_hub_clients")
#     return None  # TODO implement


@dispatcher.add_method
def mpc_hub_request(**kwargs):
    with db.lock:
        auth.verify_json(kwargs)
        verify.request_input(
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
        # FIXME verify signing pubkey matches channel client pubkey
        auth.verify_json(kwargs)
        verify.deposit_input(
            kwargs["handle"],
            kwargs["deposit_script"],
            kwargs["next_revoke_secret_hash"]
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
        # FIXME verify signing pubkey matches channel client pubkey
        auth.verify_json(kwargs)
        verify.sync_input(
            kwargs["handle"],
            kwargs["next_revoke_secret_hash"],
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
        return rpc.counterparty_call(method, kwargs)
    dispatcher[method] = counterparty_method
    return counterparty_method


create_send = _add_cp_call("create_send")
getrawtransaction = _add_cp_call("getrawtransaction")
sendrawtransaction = _add_cp_call("sendrawtransaction")
get_unspent_txouts = _add_cp_call("get_unspent_txouts")
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
