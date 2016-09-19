# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
from picopayments import etc
from picopayments import RPC
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import sign_deposit
from counterpartylib.lib.micropayments.scripts import sign_created_commit


class MpcClient(object):

    def __init__(self, url=None, auth_wif=None,
                 username=None, password=None, verify_ssl_cert=True):
        if url is None:
            url = "https://127.0.0.1:{0}/api/".format(etc.port)
        self.rpc = RPC(url, auth_wif=auth_wif, username=username,
                       password=password, verify_ssl_cert=False)

    def get_rawtx(self, txid):
        """TODO doc string"""
        return self.rpc.getrawtransaction(tx_hash=txid)

    def get_balances(self, address, assets=None):
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

    def block_send(self, dryrun=False, **kwargs):
        """TODO doc string"""

        # replace source wif with address
        wif = kwargs.pop("source")
        kwargs["source"] = util.wif2address(wif)

        # create, sign and publish transaction
        unsigned_rawtx = self.rpc.create_send(**kwargs)
        signed_rawtx = self.sign(unsigned_rawtx, wif)
        return self.publish(signed_rawtx, dryrun=dryrun)

    def sign(self, unsigned_rawtx, wif):
        """TODO doc string"""

        return sign_deposit(self.get_rawtx, wif, unsigned_rawtx)

    def publish(self, rawtx, dryrun=False):
        if dryrun:
            return util.gettxid(rawtx)
        return self.rpc.sendrawtransaction(tx_hex=rawtx)  # pragma: no cover

    def create_signed_commit(self, wif, state, quantity,
                             revoke_secret_hash, delay_time):

        # create commit
        result = self.rpc.mpc_create_commit(
            state=state, revoke_secret_hash=revoke_secret_hash,
            delay_time=delay_time, quantity=quantity
        )
        state = result["state"]
        commit_script = result["commit_script"]
        unsigned_rawtx = result["tosign"]["commit_rawtx"]
        deposit_script_hex = result["tosign"]["deposit_script"]

        # sign commit
        signed_rawtx = sign_created_commit(
            self.get_rawtx, wif, unsigned_rawtx, deposit_script_hex
        )

        # replace unsigned rawtx of state commit with signed rawtx
        for commit in state["commits_active"]:
            if commit["script"] == commit_script:
                commit["rawtx"] = signed_rawtx

        return {
            "state": state,
            "commit": {"rawtx": signed_rawtx, "script": commit_script}
        }

    def full_duplex_transfer(self, wif, get_secret_func, send_state,
                             recv_state, quantity,
                             send_next_revoke_secret_hash,
                             send_commit_delay_time):
        commit = None
        revokes = []

        # revoke what we can to maximize liquidity
        recv_moved_before = self.rpc.mpc_transferred_amount(state=recv_state)
        if recv_moved_before > 0:
            revoke_until_quantity = max(recv_moved_before - quantity, 0)

            # get hashes of secrets to publish
            revoke_hashes = self.rpc.mpc_revoke_hashes_until(
                state=recv_state, quantity=revoke_until_quantity,
                surpass=False  # never revoke past the given quantity!!!
            )

            # get secrets to publish
            revokes += [get_secret_func(h) for h in revoke_hashes]

            # revoke commits for secrets that will be published
            recv_state = self.rpc.mpc_revoke_all(state=recv_state,
                                                 secrets=revokes)

        # create commit to send the rest
        recv_moved_after = self.rpc.mpc_transferred_amount(state=recv_state)
        recv_revoked_quantity = recv_moved_before - recv_moved_after
        send_quantity = quantity - recv_revoked_quantity
        if send_quantity > 0:
            result = self.create_signed_commit(
                wif, send_state, send_quantity,
                send_next_revoke_secret_hash,
                send_commit_delay_time
            )
            send_state = result["state"]
            commit = result["commit"]

        return {
            "send_state": send_state, "recv_state": recv_state,
            "revokes": revokes, "commit": commit
        }

    def recover_payout(self, get_wif_func, get_secret_func, payout_rawtx,
                       commit_script, dryrun=False):
        script = util.h2b(commit_script)
        pubkey = scripts.get_commit_payee_pubkey(script)
        wif = get_wif_func(pubkey=util.b2h(pubkey))
        spend_secret_hash = scripts.get_commit_spend_secret_hash(script)
        spend_secret = get_secret_func(spend_secret_hash)
        signed_rawtx = scripts.sign_payout_recover(
            self.get_rawtx, wif, payout_rawtx, script, spend_secret
        )
        return publish(signed_rawtx, dryrun=dryrun)

    def recover_revoked(self, get_wif_func, revoke_rawtx, commit_script,
                        revoke_secret, dryrun=False):
        script = util.h2b(commit_script)
        pubkey = scripts.get_commit_payer_pubkey(script)
        wif = get_wif_func(pubkey=util.b2h(pubkey))
        signed_rawtx = scripts.sign_revoke_recover(
            self.get_rawtx, wif, revoke_rawtx, script, revoke_secret
        )
        return publish(signed_rawtx, dryrun=dryrun)

    def recover_change(self, get_wif_func, change_rawtx, deposit_script,
                       spend_secret, dryrun=False):
        script = util.h2b(deposit_script)
        pubkey = scripts.get_deposit_payer_pubkey(script)
        wif = get_wif_func(pubkey=util.b2h(pubkey))
        signed_rawtx = scripts.sign_change_recover(
            self.get_rawtx, wif, change_rawtx, script, spend_secret
        )
        return publish(signed_rawtx, dryrun=dryrun)

    def recover_expired(self, get_wif_func, expire_rawtx,
                        deposit_script, dryrun=False):
        script = util.h2b(deposit_script)
        pubkey = scripts.get_deposit_payer_pubkey(script)
        wif = get_wif_func(pubkey=util.b2h(pubkey))
        signed_rawtx = scripts.sign_expire_recover(
            self.get_rawtx, wif, expire_rawtx, script
        )
        return publish(self, signed_rawtx, dryrun=dryrun)

    def finalize_commit(self, get_wif_func, state, dryrun=False):
        commit = self.rpc.mpc_highest_commit(state=state)
        if commit is None:
            return None
        script = util.h2b(commit["script"])
        rawtx = commit["rawtx"]
        pubkey = scripts.get_commit_payee_pubkey(script)
        wif = get_wif_func(pubkey=util.b2h(pubkey))
        signed_rawtx = scripts.sign_finalize_commit(self.get_rawtx, wif,
                                                    rawtx, script)
        return publish(signed_rawtx, dryrun=dryrun)

    def full_duplex_recover_funds(self, get_wif_func, get_secret_func,
                                  recv_state, send_state, dryrun=False):
        txs = []
        for ptx in self.rpc.mpc_payouts(state=recv_state):
            txs += self.recover_payout(
                get_wif_func=get_wif_func, get_secret_func=get_secret_func,
                dryrun=dryrun, **ptx
            )
        rtxs = self.rpc.mpc_recoverables(state=send_state)
        for rtx in rtxs["revoke"]:
            txs += self.recover_revoke(
                get_wif_func=get_wif_func, dryrun=dryrun, **ptx
            )
        for ctx in rtxs["change"]:
            txs += self.recover_change(
                get_wif_func=get_wif_func, dryrun=dryrun, **ptx
            )
        for etx in rtxs["expire"]:
            txs += self.recover_expired(
                get_wif_func=get_wif_func, dryrun=dryrun, **ptx
            )
        return txs


class HubClient(MpcClient):

    _SERIALIZABLE_ATTRS = [
        "asset",  # set once
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

    def __init__(self, *args, **kwargs):
        super(HubClient, self).__init__(*args, **kwargs)
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

    def is_connected(self):
        """Returns True if connected to a hub."""
        return bool(self.handle)

    def connect(self, quantity, expire_time=1024, asset="XCP",
                delay_time=2, own_url=None, dryrun=False):
        """TODO doc string"""

        assert(not self.is_connected())
        self.asset = asset
        self.client_wif = self.rpc.auth_wif
        self.own_url = own_url
        self.client_pubkey = util.wif2pubkey(self.client_wif)
        self.c2h_deposit_expire_time = expire_time
        self.c2h_deposit_quantity = quantity
        next_revoke_hash = self._create_initial_secrets()
        self._request_connection()
        self._validate_matches_terms()
        c2h_deposit_rawtx = self._make_deposit()
        h2c_deposit_script = self._exchange_deposit_scripts(next_revoke_hash)
        signed_rawtx = self.sign(c2h_deposit_rawtx, self.client_wif)
        c2h_deposit_txid = self.publish(signed_rawtx, dryrun=dryrun)
        self._set_initial_h2c_state(h2c_deposit_script)
        self._add_to_commits_requested(next_revoke_hash)
        self.payments_sent = []
        self.payments_received = []
        self.payments_queued = []
        self.c2h_commit_delay_time = delay_time
        return c2h_deposit_txid

    def micro_send(self, handle, quantity, token=None):
        """TODO doc string"""

        assert(self.is_connected())
        if token is None:
            token = util.b2h(os.urandom(32))
        self.payments_queued.append({
            "payee_handle": handle,
            "amount": quantity,
            "token": token
        })
        return token

    def get_status(self, clearance=6):
        assert(self.is_connected())
        asset = self.asset
        netcode = util.wif2netcode(self.client_wif)
        h2c_expired = self.rpc.mpc_deposit_expired(
            state=self.h2c_state, clearance=clearance
        )
        c2h_expired = self.rpc.mpc_deposit_expired(
            state=self.c2h_state, clearance=clearance
        )
        c2h_deposit_address = util.script2address(
            util.h2b(self.c2h_state["deposit_script"]), netcode=netcode
        )
        c2h_deposit = self.get_balances(c2h_deposit_address, [asset])[asset]
        h2c_deposit_address = util.script2address(
            util.h2b(self.h2c_state["deposit_script"]), netcode=netcode
        )
        h2c_deposit = self.get_balances(h2c_deposit_address, [asset])[asset]
        c2h_transferred = self.rpc.mpc_transferred_amount(state=self.c2h_state)
        h2c_transferred = self.rpc.mpc_transferred_amount(state=self.h2c_state)
        return {
            "asset": asset,
            "netcode": netcode,
            "c2h_expired": c2h_expired,
            "h2c_expired": h2c_expired,
            "balance": c2h_deposit + h2c_transferred - c2h_transferred,
            "c2h_deposit_quantity": c2h_deposit,
            "h2c_deposit_quantity": h2c_deposit,
            "c2h_transferred_quantity": c2h_transferred,
            "h2c_transferred_quantity": h2c_transferred,
        }

    def _add_to_commits_requested(self, secret_hash):
        # emulates mpc_request_commit api call
        self.h2c_state["commits_requested"].append(secret_hash)

    def _gen_secret(self):
        secret_value = util.b2h(os.urandom(32))
        secret_hash = util.hash160hex(secret_value)
        self.secrets[secret_hash] = secret_value
        return secret_hash

    def sync(self):
        """TODO doc string"""

        assert(self.is_connected())
        payments = self.payments_queued
        self.payments_queued = []

        # transfer payment funds (create commit/revokes)
        sync_fee = self.channel_terms["sync_fee"]
        quantity = sum([p["amount"] for p in payments]) + sync_fee
        result = self.full_duplex_transfer(
            self.client_wif, self.secrets.get, self.c2h_state,
            self.h2c_state, quantity, self.c2h_next_revoke_secret_hash,
            self.c2h_commit_delay_time
        )
        commit = result["commit"]
        revokes = result["revokes"]
        self.h2c_state = result["recv_state"]
        self.c2h_state = result["send_state"]

        # create next revoke secret for h2c channel
        h2c_next_revoke_secret_hash = self._gen_secret()
        self._add_to_commits_requested(h2c_next_revoke_secret_hash)

        # sync with hub
        result = self.rpc.mph_sync(
            next_revoke_secret_hash=h2c_next_revoke_secret_hash,
            handle=self.handle, sends=payments, commit=commit, revokes=revokes
        )
        h2c_commit = result["commit"]
        c2h_revokes = result["revokes"]
        receive_payments = result["receive"]
        self.c2h_next_revoke_secret_hash = result["next_revoke_secret_hash"]

        # add commit to h2c channel
        if h2c_commit:
            self.h2c_state = self.rpc.mpc_add_commit(
                state=self.h2c_state,
                commit_rawtx=h2c_commit["rawtx"],
                commit_script=h2c_commit["script"]
            )

        # add c2h revokes to channel
        if c2h_revokes:
            self.c2h_state = self.rpc.mpc_revoke_all(
                state=self.c2h_state, secrets=c2h_revokes
            )

        return receive_payments

    def _create_initial_secrets(self):
        self.secrets = {}
        self.h2c_spend_secret_hash = self._gen_secret()
        return self._gen_secret()

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
            handle=self.handle, asset=self.asset,
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

    def _validate_matches_terms(self):
        expire_max = self.channel_terms["expire_max"]
        deposit_max = self.channel_terms["deposit_max"]
        expire_time = self.c2h_deposit_expire_time
        quantity = self.c2h_deposit_quantity
        assert(expire_max == 0 or expire_time <= expire_max)
        assert(deposit_max == 0 or quantity <= deposit_max)

    def _set_initial_h2c_state(self, h2c_deposit_script):
        self.h2c_state = {
            "asset": self.asset,
            "deposit_script": h2c_deposit_script,
            "commits_requested": [],
            "commits_active": [],
            "commits_revoked": [],
        }
