# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
from picopayments import etc
from picopayments import RPC
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import sign_deposit
from counterpartylib.lib.micropayments.scripts import sign_created_commit


class Client(object):

    _SERIALIZABLE_ATTRS = [
        "handle",  # set once
        "channel_terms",  # set once
        "client_wif",  # set once
        "client_pubkey",  # set once
        "hub_pubkey",  # set once
        "secrets",  # append only
        "c2h_state",  # mutable
        "c2h_spend_secret_hash",  # set once
        "c2h_commit_delay_time",  # set once
        "c2h_next_revoke_secret_hash",  # mutable
        "c2h_deposit_expire_time",  # set once
        "c2h_deposit_quantity",  # set once
        "h2c_state",  # set once
        "payments_sent",
        "payments_received",
        "payments_queued",
    ]

    def __init__(self, url=None, auth_wif=None,
                 username=None, password=None, verify_ssl_cert=True):
        if url is None:
            url = "https://127.0.0.1:{0}/api/".format(etc.port)
        self.rpc = RPC(url, auth_wif=auth_wif, username=username,
                       password=password, verify_ssl_cert=False)
        for attr in self._SERIALIZABLE_ATTRS:
            setattr(self, attr, None)

    @classmethod
    def deserialize(cls, data):
        """TODO doc string"""
        obj = cls(**data["hub"])
        for attr in obj._SERIALIZABLE_ATTRS:
            setattr(obj, attr, data[attr])
        return obj

    def serialize(self):
        """TODO doc string"""
        data = {
            "hub": {
                "url": self.rpc.url,
                "auth_wif": self.rpc.auth_wif,
                "username": self.rpc.username,
                "password": self.rpc.password,
                "verify_ssl_cert": self.rpc.verify_ssl_cert,
            }
        }
        for attr in self._SERIALIZABLE_ATTRS:
            data[attr] = getattr(self, attr)
        return data

    def get_tx(self, txid):
        """TODO doc string"""
        return self.rpc.getrawtransaction(tx_hash=txid)

    def balance(self):
        """TODO doc string"""

        assert(self.connected())
        # TODO return {"btc": value, "asset": value}
        # TODO implement

    def balances(self, address, assets=None):
        """TODO doc string"""

        # FIXME include BTC balance
        entries = self.rpc.get_balances(filters=[
            {"field": "address", "op": "==", "value": address},
        ])
        result = {}
        for entrie in entries:
            if assets and entrie["asset"] not in assets:
                continue
            result[entrie["asset"]] = entrie["quantity"]
        return result

    def block_send(self, publish_tx=True, **kwargs):
        """TODO doc string"""

        # replace source wif with address
        wif = kwargs.pop("source")
        kwargs["source"] = util.wif2address(wif)

        # create and sign transaction
        unsigned_rawtx = self.rpc.create_send(**kwargs)
        return self.sign_and_publish(unsigned_rawtx, wif,
                                     publish_tx=publish_tx)

    def sign(self, unsigned_rawtx, wif):
        """TODO doc string"""

        return sign_deposit(self.get_tx, wif, unsigned_rawtx)

    def sign_and_publish(self, unsigned_rawtx, wif, publish_tx=True):
        """TODO doc string"""

        # FIXME remove this method
        signed_rawtx = self.sign(unsigned_rawtx, wif)
        return self.publish(signed_rawtx, publish_tx=publish_tx)

    def micro_send(self, handle, quantity, token=None):
        """TODO doc string"""

        assert(self.connected())
        if token is None:
            token = util.b2h(os.urandom(32))
        self.payments_queued.append({
            "payee_handle": handle,
            "amount": quantity,
            "token": token
        })
        return token

    # def sync(self):
    #     """TODO doc string"""
    #
    #     assert(self.connected())
    #     pass  # FIXME implement

    def connected(self):
        """Returns True if connected to a hub"""
        return bool(self.handle)

    def create_commit(self, quantity):
        """TODO doc string"""

        assert(self.connected())
        result = self.rpc.mpc_create_commit(
            state=self.c2h_state,
            quantity=quantity,
            revoke_secret_hash=self.c2h_next_revoke_secret_hash,
            delay_time=self.c2h_commit_delay_time
        )
        script = result["commit_script"]
        rawtx = sign_created_commit(
            self.get_tx,
            self.client_wif,
            result["tosign"]["commit_rawtx"],
            result["tosign"]["deposit_script"],
        )
        return {"rawtx": rawtx, "script": script}

    def connect(self, quantity, expire_time=1024, asset="XCP",
                delay_time=2, own_url=None, publish_tx=True):
        """TODO doc string"""

        assert(not self.connected())
        self.asset = asset
        self.client_wif = self.rpc.auth_wif
        self.own_url = own_url
        self.client_pubkey = util.wif2pubkey(self.client_wif)
        self.c2h_deposit_expire_time = expire_time
        self.c2h_deposit_quantity = quantity
        h2c_next_revoke_secret_hash = self._create_initial_secrets()
        self._request_connection()
        self._validate_matches_terms()
        c2h_deposit_rawtx = self._make_deposit()
        h2c_deposit_script = self._exchange_deposit_scripts(
            h2c_next_revoke_secret_hash
        )
        c2h_deposit_txid = self.sign_and_publish(
            c2h_deposit_rawtx, self.client_wif, publish_tx=publish_tx
        )
        self._set_initial_h2c_state(h2c_deposit_script)
        self.payments_sent = []
        self.payments_received = []
        self.payments_queued = []
        self.c2h_commit_delay_time = delay_time
        return c2h_deposit_txid

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
        result = self.rpc.mph_request(
            asset=self.asset, url=self.own_url,
            spend_secret_hash=self.h2c_spend_secret_hash
        )
        self.handle = result["handle"]
        self.channel_terms = result["channel_terms"]
        self.hub_pubkey = result["pubkey"]
        self.c2h_spend_secret_hash = result["spend_secret_hash"]

    def _exchange_deposit_scripts(self, h2c_next_revoke_secret_hash):
        result = self.rpc.mph_deposit(
            handle=self.handle,
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

    def publish(self, rawtx, publish_tx=True):
        # FIXME publish_tx -> dryrun
        if not publish_tx:
            return util.gettxid(rawtx)
        return self.rpc.sendrawtransaction(tx_hex=rawtx)  # pragma: no cover

    def _validate_matches_terms(self):
        expire_max = self.channel_terms["expire_max"]
        assert(
            expire_max == 0 or self.c2h_deposit_expire_time <= expire_max
        )
        deposit_max = self.channel_terms["deposit_max"]
        assert(
            deposit_max == 0 or self.c2h_deposit_quantity <= deposit_max
        )

    def _set_initial_h2c_state(self, h2c_deposit_script):
        self.h2c_state = {
            "asset": self.asset,
            "deposit_script": h2c_deposit_script,
            "commits_requested": [],
            "commits_active": [],
            "commits_revoked": [],
        }
