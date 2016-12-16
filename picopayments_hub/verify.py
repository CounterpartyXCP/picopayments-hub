# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import re
import jsonschema
from counterpartylib.lib.micropayments import validate
from micropayment_core import scripts
from micropayment_core import util
from picopayments_hub import err
from picopayments_hub import db
from picopayments_hub import etc
from picopayments_hub import lib
from jsonrpc import dispatcher


URL_REGEX = re.compile(

    r'^(?:http|ftp)s?://'  # http:// or https://

    # domain...
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)'
    r'+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'

    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


PAYMENT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "payee_handle": {"type": "string"},
            "amount": {"type": "number"},
            "token": {"type": "string"}
        },
        "required": ["payee_handle", "amount", "token"],
        "additionalProperties": False
    }
}


COMMIT_SCHEMA = {
    "type": "object",
    "properties": {
        "rawtx": {"type": "string"},
        "script": {"type": "string"},
    },
    "required": ["rawtx", "script"],
    "additionalProperties": False
}


REVOKES_SCHEMA = {
    "type": "array",
    "items": {"type": "string"}
}


def asset_exists(asset):
    from picopayments_hub import api
    validate.is_string(asset)
    assets = [e["asset_name"] for e in api.get_assets()]
    if asset not in assets:
        raise err.AssetDoesNotExist(asset)


def assets_exists(assets):
    for asset in assets:
        asset_exists(asset)


def handles_exist(handles):
    if not db.handles_exist(handles):
        raise err.HandlesNotFound(handles)


def is_url(url):
    if not URL_REGEX.match(url):
        raise err.InvalidUrl(url)


def c2h_commit(handle, commit_rawtx, commit_script):
    hub_connection(handle)
    netcode = "XTN" if etc.testnet else "BTC"
    c2h_channel = db.c2h_channel(handle=handle)
    validate.is_commit_rawtx(
        dispatcher, commit_rawtx, c2h_channel["asset"],
        c2h_channel["deposit_script"], commit_script, netcode
    )


def _channel_client(handle, pubkey):

    # signature was done by correct client
    c2h_channel = db.c2h_channel(handle=handle)
    expected_pubkey = c2h_channel["payer_pubkey"]
    if expected_pubkey != pubkey:
        raise err.ClientPubkeyMissmatch(expected_pubkey, pubkey)

    return c2h_channel


def terms_input(assets):
    if assets:
        assets_exists(assets)


def status_input(assets):
    if assets:
        assets_exists(assets)


def request_input(asset, pubkey, spend_secret_hash, hub_rpc_url):
    validate.pubkey(pubkey)
    validate.hash160(spend_secret_hash)
    asset_exists(asset)
    if hub_rpc_url:
        is_url(hub_rpc_url)

    # asset must be in terms
    terms = lib.get_terms().get(asset)
    if terms is None:
        raise err.AssetNotInTerms(asset)


def hub_connection(handle):
    validate.is_hex(handle)
    connection = db.hub_connection(handle=handle)
    if not connection:
        raise err.HandleNotFound(handle)
    return connection


def deposit_input(handle, deposit_script,
                  next_revoke_secret_hash, client_pubkey):

    connection = hub_connection(handle)
    if connection["complete"]:
        raise err.DepositAlreadyGiven(handle)

    # FIXME validate terms["expire_max"] >= expire time >= terms["expire_min"]
    validate.hash160(next_revoke_secret_hash)
    c2h_channel = _channel_client(handle, client_pubkey)
    expected_payee_pubkey = c2h_channel["payee_pubkey"]
    expected_spend_secret_hash = c2h_channel["spend_secret_hash"]
    validate.deposit_script(deposit_script, expected_payee_pubkey,
                            expected_spend_secret_hash)


def sync_input(handle, next_revoke_secret_hash, client_pubkey,
               payments, commit, revokes):
    hub_connection(handle)
    validate.hash160(next_revoke_secret_hash)
    _channel_client(handle, client_pubkey)

    handles = []
    if payments:
        jsonschema.validate(payments, PAYMENT_SCHEMA)
        for payment in payments:
            validate.is_hex(payment["token"])
            validate.is_hex(payment["payee_handle"])
            validate.is_quantity(payment["amount"])
            handles.append(payment["payee_handle"])

    handles_exist(handles)

    if revokes:
        jsonschema.validate(revokes, REVOKES_SCHEMA)
        # FIXME check revokes match commits?

    if commit:
        jsonschema.validate(commit, COMMIT_SCHEMA)
        c2h_commit(handle, commit["rawtx"], commit["script"])


def close_input(handle, client_pubkey, spend_secret):
    hub_connection(handle)
    _channel_client(handle, client_pubkey)

    # validate spend secret for h2c deposit
    if spend_secret is not None:
        validate.is_string(spend_secret)
        spend_secret_hash = util.hash160hex(spend_secret)
        deposit_script = db.h2c_channel(handle=handle)["deposit_script"]
        expected_hash = scripts.get_deposit_spend_secret_hash(deposit_script)
        if expected_hash != spend_secret_hash:
            raise err.InvalidSpendSecret(expected_hash, spend_secret)
