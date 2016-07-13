# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments import cfg
from picopayments import util
from picopayments import terms


@dispatcher.add_method
def mpc_hub_terms(assets=None):
    all_trems = terms.read()
    if assets:
        for key in all_trems.keys():
            if key not in assets:
                all_trems.pop(key)
    return all_trems


@dispatcher.add_method
def mpc_hub_clients(clients=None, assets=None):
    print("mpc_hub_clients")
    return None  # TODO implement


@dispatcher.add_method
def mpc_hub_request(asset, pubkey, spend_secret_hash, url=None):
    print("mpc_hub_request")
    return None  # TODO implement


@dispatcher.add_method
def mpc_hub_deposit(channel_handle, deposit_script, unused_revoke_secret_hash):
    print("mpc_hub_deposit")
    return None  # TODO implement


@dispatcher.add_method
def mpc_hub_sync(channel_handle, unused_revoke_secret_hash,
                 send=None, commit=None, revokes=None):
    print("mpc_hub_sync")
    return None  # TODO implement


def _add_counterparty_call(method):

    def counterparty_method(**kwargs):
        return util.rpccall(
            cfg.counterparty_url, method, kwargs,
            cfg.counterparty_username, cfg.counterparty_password
        )
    dispatcher[method] = counterparty_method


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
