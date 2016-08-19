# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import re
import jsonschema
from counterpartylib.lib.micropayments import validate
from picopayments import err
from picopayments import db
from picopayments import cfg
from picopayments import rpc
from picopayments import ctrl


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
            "payer_handle": {"type": "string"},
            "payee_handle": {"type": "string"},
            "amount": {"type": "number"},
            "token": {"type": "string"}
        },
        "required": ["payer_handle", "payee_handle", "amount", "token"],
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


def is_url(url):
    if not URL_REGEX.match(url):
        raise err.InvalidUrl(url)


def request_input(asset, pubkey, spend_secret_hash, hub_rpc_url):
    validate.pubkey(pubkey)
    validate.hash160(spend_secret_hash)
    if hub_rpc_url:
        is_url(hub_rpc_url)

    # asset must be in terms
    all_terms = ctrl.terms()
    if asset not in all_terms:
        raise err.AssetNotInTerms(asset)


def deposit_input(handle, deposit_script, next_revoke_secret_hash):
    validate.is_hex(handle)
    validate.hash160(next_revoke_secret_hash)
    client2hub_channel = db.receive_channel(handle)
    # FIXME verify signing pubkey matches channel client pubkey
    if not client2hub_channel:
        raise err.HandleNotFound(handle)
    expected_payee_pubkey = client2hub_channel["payee_pubkey"]
    expected_spend_secret_hash = client2hub_channel["spend_secret_hash"]
    validate.deposit_script(deposit_script, expected_payee_pubkey,
                            expected_spend_secret_hash)
    if client2hub_channel["meta_complete"]:
        raise err.DepositAlreadyGiven(handle)


def is_client2hub_commit(handle, commit_rawtx, commit_script):
    netcode = "XTN" if cfg.testnet else "BTC"
    client2hub_channel = db.receive_channel(handle)
    deposit_utxos = rpc.cp_call(
        method="get_unspent_txouts",
        params={"address": client2hub_channel["deposit_address"]}
    )
    validate.commit_rawtx(
        deposit_utxos, commit_rawtx, client2hub_channel["asset"],
        client2hub_channel["deposit_script"], commit_script, netcode
    )


def sync_input(handle, next_revoke_secret_hash, sends, commit, revokes):
    validate.is_hex(handle)
    validate.hash160(next_revoke_secret_hash)
    handles = [handle]

    if sends:
        jsonschema.validate(sends, PAYMENT_SCHEMA)
        for send in sends:
            validate.is_hex(send["token"])
            validate.is_hex(send["payee_handle"])
            validate.is_hex(send["payer_handle"])
            validate.is_quantity(send["amount"])
            handles += [send["payer_handle"], send["payee_handle"]]

    # make sure all handles actually exist
    if not db.handles_exist(handles):
        raise err.HandlesNotFound(handles)

    # FIXME verify signing pubkey matches channel client pubkey

    if revokes:
        jsonschema.validate(revokes, REVOKES_SCHEMA)
        # FIXME check revokes match commits?

    if commit:
        jsonschema.validate(commit, COMMIT_SCHEMA)
        is_client2hub_commit(handle, commit["rawtx"], commit["script"])
