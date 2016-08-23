# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
from picopayments.rpc import RPC
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import sign_deposit


class Client(object):

    _SERIALIZABLE_PROPS = [
        "handle",
        "channel_terms",
        "client_wif",
        "client_pubkey",
        "hub_pubkey",
        "secrets",  # append only
        "c2h_state",  # mutable
        "c2h_spend_secret_hash",
        "c2h_next_revoke_secret_hash",  # mutable
        "c2h_deposit_expire_time",
        "c2h_deposit_quantity",
        "h2c_state",
    ]

    def __init__(self, url, auth_wif=None, username=None,
                 password=None, verify_ssl_cert=True):
        self.rpc = RPC(url, auth_wif=auth_wif, username=username,
                       password=password, verify_ssl_cert=False)

    @classmethod
    def deserialize(cls, data):
        obj = cls(**data["hub"])
        # FIXME batch set attributes
        return obj

    def serialize(self):
        return {
            "hub": {
                "url": self.rpc.url,
                "auth_wif": self.rpc.auth_wif,
                "username": self.rpc.username,
                "password": self.rpc.password,
                "verify_ssl_cert": self.rpc.verify_ssl_cert,
            },
            # FIXME batch get attributes
        }

    def get_tx(self, txid):
        return self.rpc.getrawtransaction(tx_hash=txid)

    def send(self, src_wif, dest_address, asset, quantity, publish_tx=True):
        src_address = util.wif2address(src_wif)
        unsigned_rawtx = self.rpc.create_send(
            source=src_address, destination=dest_address,
            quantity=quantity, asset=asset, regular_dust_size=200000,
        )
        signed_rawtx = sign_deposit(self.get_tx, src_wif, unsigned_rawtx)
        if publish_tx:
            return self.rpc.sendrawtransaction(tx_hex=signed_rawtx)
        return None

    def open_connection(self, deposit_quantity, deposit_expire_time,
                        netcode="BTC", asset="XCP",
                        own_url=None, publish_tx=True):

        self.asset = asset
        self.client_wif = self.rpc.auth_wif
        self.own_url = own_url
        self.client_pubkey = util.wif2pubkey(self.client_wif)
        self.c2h_deposit_expire_time = deposit_expire_time
        self.c2h_deposit_quantity = deposit_quantity
        h2c_next_revoke_secret_hash = self._create_initial_secrets()
        self._request_connection()
        self._validate_matches_terms()
        c2h_deposit_rawtx = self._make_deposit()
        h2c_deposit_script = self._exchange_deposit_scripts(
            h2c_next_revoke_secret_hash
        )
        self._sign_and_publish_deposit(c2h_deposit_rawtx, publish_tx)
        self.h2c_state = {
            "asset": self.asset,
            "deposit_script": h2c_deposit_script,
            "commits_requested": [],
            "commits_active": [],
            "commits_revoked": [],
        }

    def _create_initial_secrets(self):
        h2c_spend_secret_value = util.b2h(os.urandom(32))
        self.h2c_spend_secret_hash = util.hash160hex(h2c_spend_secret_value)
        h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
        h2c_next_revoke_secret_hash = util.hash160hex(
            h2c_next_revoke_secret_value
        )
        self.secrets = {
            self.h2c_spend_secret_hash: h2c_spend_secret_value,
            h2c_next_revoke_secret_hash: h2c_next_revoke_secret_value
        }
        return h2c_next_revoke_secret_hash

    def _request_connection(self):
        result = self.rpc.mpc_hub_request(
            asset=self.asset, url=self.own_url,
            spend_secret_hash=self.h2c_spend_secret_hash
        )
        self.handle = result["handle"]
        self.channel_terms = result["channel_terms"]
        self.hub_pubkey = result["pubkey"]
        self.c2h_spend_secret_hash = result["spend_secret_hash"]

    def _exchange_deposit_scripts(self, h2c_next_revoke_secret_hash):
        result = self.rpc.mpc_hub_deposit(
            asset=self.asset,
            deposit_script=self.c2h_state["deposit_script"],
            next_revoke_secret_hash=h2c_next_revoke_secret_hash
        )
        h2c_deposit_script = result["deposit_script"]
        self.c2h_next_revoke_secret_hash = result["next_revoke_secret_hash"]
        return h2c_deposit_script

    def _make_deposit(self):
        result = self.rpc.mpc_make_deposit(
            asset=self.asset,
            payer_pubkey=self.client_pubkey,
            payee_pubkey=self.hub_pubkey,
            spend_secret_hash=self.c2h_spend_secret_hash,
            expire_time=self.c2h_deposit_expire_time,
            quantity=self.c2h_deposit_quantity
        )
        self.c2h_state = result["state"]
        return result["topublish"]

    def _sign_and_publish_deposit(self, c2h_deposit_rawtx, publish_tx):
        signed_c2h_deposit_rawtx = sign_deposit(
            self.get_tx, self.client_wif, c2h_deposit_rawtx
        )
        if publish_tx:
            self.rpc.sendrawtransaction(tx_hex=signed_c2h_deposit_rawtx)

    def _validate_matches_terms(self):
        timeout_limit = self.channel_terms["timeout_limit"]
        if timeout_limit != 0:
            assert(self.c2h_deposit_expire_time <= timeout_limit)
        deposit_limit = self.channel_terms["deposit_limit"]
        if deposit_limit != 0:
            assert(self.c2h_deposit_quantity <= deposit_limit)
