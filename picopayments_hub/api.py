# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


from jsonrpc import dispatcher
from picopayments_hub import etc
from picopayments_hub import verify
from picopayments_hub import lib
from picopayments_cli import auth
from picopayments_cli.rpc import jsonrpc_call


@dispatcher.add_method
def mph_status(assets=None):
    with etc.database_lock:
        verify.status_input(assets)
        return {
            "liquidity": lib.get_hub_liquidity(assets=assets),
            "current_terms": lib.get_terms(assets=assets),
            "connections": lib.get_connections_status(assets=assets),
            "funding_addresses": lib.get_funding_addresses(assets=assets)
        }


@dispatcher.add_method
def mph_request(**kwargs):
    with etc.database_lock:
        auth.verify_json(kwargs)
        verify.request_input(
            kwargs["asset"],
            kwargs["pubkey"],
            kwargs["spend_secret_hash"],
            kwargs.get("hub_rpc_url")
        )
        result, authwif = lib.create_hub_connection(
            kwargs["asset"],
            kwargs["pubkey"],
            kwargs["spend_secret_hash"],
            kwargs.get("hub_rpc_url")
        )
        return auth.sign_json(result, authwif)


@dispatcher.add_method
def mph_deposit(**kwargs):
    with etc.database_lock:
        auth.verify_json(kwargs)
        verify.deposit_input(
            kwargs["handle"],
            kwargs["deposit_script"],
            kwargs["next_revoke_secret_hash"],
            kwargs["pubkey"]
        )
        result, authwif = lib.complete_connection(
            kwargs["handle"],
            kwargs["deposit_script"],
            kwargs["next_revoke_secret_hash"]
        )
        return auth.sign_json(result, authwif)


@dispatcher.add_method
def mph_sync(**kwargs):
    with etc.database_lock:
        auth.verify_json(kwargs)
        verify.sync_input(
            kwargs["handle"],
            kwargs["next_revoke_secret_hash"],
            kwargs["pubkey"],
            kwargs.get("sends"),
            kwargs.get("commit"),
            kwargs.get("revokes")
        )
        result, authwif = lib.sync_hub_connection(
            kwargs["handle"],
            kwargs["next_revoke_secret_hash"],
            kwargs.get("sends"),
            kwargs.get("commit"),
            kwargs.get("revokes")
        )
        return auth.sign_json(result, authwif)


@dispatcher.add_method
def mph_close(**kwargs):
    with etc.database_lock:
        auth.verify_json(kwargs)
        verify.close_input(
            kwargs["handle"],
            kwargs["pubkey"],
            kwargs.get("spend_secret"),
        )
        result, authwif = lib.close_connection(
            kwargs["handle"],
            kwargs.get("spend_secret"),
        )
        return auth.sign_json(result, authwif)


def _cplib_call(method, params={}):
    return jsonrpc_call(
        etc.counterparty_url, method, params=params,
        username=etc.counterparty_username,
        password=etc.counterparty_password
    )


def _make_cplib_call(method):
    def counterparty_method(**kwargs):
        return _cplib_call(method=method, params=kwargs)
    dispatcher[method] = counterparty_method
    return counterparty_method


@dispatcher.add_method
def create_send(**kwargs):
    kwargs["disable_utxo_locks"] = True  # always disable
    return _cplib_call(method="create_send", params=kwargs)


search_raw_transactions = _make_cplib_call("search_raw_transactions")
get_tx_info = _make_cplib_call("get_tx_info")
unpack = _make_cplib_call("unpack")
get_unspent_txouts = _make_cplib_call("get_unspent_txouts")
getrawtransaction = _make_cplib_call("getrawtransaction")
getrawtransaction_batch = _make_cplib_call("getrawtransaction_batch")
get_unspent_txouts = _make_cplib_call("get_unspent_txouts")
get_balances = _make_cplib_call("get_balances")
create_issuance = _make_cplib_call("create_issuance")
get_assets = _make_cplib_call("get_assets")
sendrawtransaction = _make_cplib_call("sendrawtransaction")
mpc_make_deposit = _make_cplib_call("mpc_make_deposit")
mpc_set_deposit = _make_cplib_call("mpc_set_deposit")
mpc_request_commit = _make_cplib_call("mpc_request_commit")
mpc_create_commit = _make_cplib_call("mpc_create_commit")
mpc_add_commit = _make_cplib_call("mpc_add_commit")
mpc_revoke_hashes_until = _make_cplib_call("mpc_revoke_hashes_until")
mpc_revoke_all = _make_cplib_call("mpc_revoke_all")
mpc_highest_commit = _make_cplib_call("mpc_highest_commit")
mpc_transferred_amount = _make_cplib_call("mpc_transferred_amount")
mpc_payouts = _make_cplib_call("mpc_payouts")
mpc_recoverables = _make_cplib_call("mpc_recoverables")
mpc_deposit_ttl = _make_cplib_call("mpc_deposit_ttl")
mpc_published_commits = _make_cplib_call("mpc_published_commits")
