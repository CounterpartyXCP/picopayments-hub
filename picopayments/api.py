# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from . import ctrl
from . import terms
from . import validate


@dispatcher.add_method
def mpc_hub_terms(assets=None):
    all_trems = terms.read()
    if assets:
        for key in list(all_trems.keys())[:]:
            if key not in assets:
                all_trems.pop(key)
    return all_trems


@dispatcher.add_method
def mpc_hub_clients(clients=None, assets=None):
    # FIXME validate input
    print("mpc_hub_clients")
    return None  # TODO implement


@dispatcher.add_method
def mpc_hub_request(asset, pubkey, spend_secret_hash, hub_rpc_url=None):
    validate.request_input(asset, pubkey, spend_secret_hash, hub_rpc_url)
    return ctrl.create_hub_connection(
        asset, pubkey, spend_secret_hash, hub_rpc_url
    )


@dispatcher.add_method
def mpc_hub_deposit(handle, deposit_script, next_revoke_secret_hash):
    validate.deposit_input(handle, deposit_script, next_revoke_secret_hash)
    return ctrl.complete_connection(handle, deposit_script,
                                    next_revoke_secret_hash)


@dispatcher.add_method
def mpc_hub_sync(handle, next_revoke_secret_hash,
                 sends=None, commit=None, revokes=None):
    validate.sync_input(handle, next_revoke_secret_hash,
                        sends, commit, revokes)
    return ctrl.sync_hub_connection(handle, next_revoke_secret_hash,
                                    sends, commit, revokes)


def _add_counterparty_call(method):
    def counterparty_method(**kwargs):
        return ctrl.counterparty_call(method, kwargs)
    dispatcher[method] = counterparty_method


_add_counterparty_call("get_unspent_txouts")
_add_counterparty_call("mpc_make_deposit")
_add_counterparty_call("mpc_set_deposit")
_add_counterparty_call("mpc_request_commit")
_add_counterparty_call("mpc_create_commit")
_add_counterparty_call("mpc_add_commit")
_add_counterparty_call("mpc_revoke_secret_hashes_above")
_add_counterparty_call("mpc_revoke_all")
_add_counterparty_call("mpc_heighest_commit")
_add_counterparty_call("mpc_transferred_amount")
_add_counterparty_call("mpc_payouts")
_add_counterparty_call("mpc_recoverables")


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')
