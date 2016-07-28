# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import re
import jsonschema
from counterpartylib.lib.micropayments import validate
from . import exceptions
from . import terms
from . import database as db
from . import config
from . import control


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
        raise exceptions.InvalidUrl(url)


def request_input(asset, pubkey, spend_secret_hash, hub_rpc_url):
    validate.pubkey(pubkey)
    validate.hash160(spend_secret_hash)
    if hub_rpc_url:
        is_url(hub_rpc_url)

    # asset must be in terms
    all_terms = terms.read()
    if asset not in all_terms:
        raise exceptions.AssetNotInTerms(asset)


def deposit_input(handle, deposit_script, next_revoke_secret_hash):
    validate.is_hex(handle)
    validate.hash160(next_revoke_secret_hash)
    recv_channel = db.receive_channel(handle)
    if not recv_channel:
        raise exceptions.HandleNotFound(handle)
    expected_payee_pubkey = recv_channel["payee_pubkey"]
    expected_spend_secret_hash = recv_channel["spend_secret_hash"]
    validate.deposit_script(deposit_script, expected_payee_pubkey,
                            expected_spend_secret_hash)
    if recv_channel["meta_complete"]:
        raise exceptions.DepositAlreadyGiven(handle)


def is_recv_commit(handle, commit_rawtx, commit_script):
    netcode = "XTN" if config.testnet else "BTC"
    recv_channel = db.receive_channel(handle)
    deposit_utxos = control.counterparty_call(
        method="get_unspent_txouts",
        params={"address": recv_channel["deposit_address"]}
    )
    validate.commit_rawtx(
        deposit_utxos, commit_rawtx, recv_channel["asset"],
        recv_channel["deposit_script"], commit_script, netcode
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
            # FIXME validate assets match on both ends

    # make sure all handles actually exist
    if not db.handles_exist(handles):
        raise exceptions.HandlesNotFound(handles)

    if revokes:
        jsonschema.validate(sends, REVOKES_SCHEMA)

    if commit:
        jsonschema.validate(commit, COMMIT_SCHEMA)
        is_recv_commit(handle, commit["rawtx"], commit["script"])
