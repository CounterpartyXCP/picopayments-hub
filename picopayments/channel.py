# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import copy
import pycoin
import time
import json
import requests
from btctxstore import BtcTxStore
from requests.auth import HTTPBasicAuth
from bitcoinrpc.authproxy import AuthServiceProxy
from collections import defaultdict
from picopayments import util
from picopayments import validate
from picopayments.scripts import get_commit_revoke_secret_hash
from picopayments.scripts import get_deposit_spend_secret_hash
from picopayments.scripts import get_deposit_payee_pubkey
from picopayments.scripts import get_commit_spend_secret_hash
from picopayments.scripts import get_commit_payee_pubkey
from picopayments.scripts import get_commit_delay_time
from picopayments import exceptions
from picopayments import scripts
from picopayments.scripts import get_deposit_expire_time
from picopayments.scripts import get_deposit_payer_pubkey
from picopayments.scripts import compile_commit_script
from picopayments.scripts import compile_deposit_script
from picopayments.scripts import DepositScriptHandler


# FIXME fees per kb, auto adjust to market price or get from counterparty
DEFAULT_TXFEE = 10000  # FIXME dont hardcode tx fee
DEFAULT_DUSTSIZE = 5430  # FIXME dont hardcode dust size
DEFAULT_TESTNET = False
DEFAULT_COUNTERPARTY_RPC_MAINNET_URL = "http://public.coindaddy.io:4000/api/"
DEFAULT_COUNTERPARTY_RPC_TESTNET_URL = "http://public.coindaddy.io:14000/api/"
DEFAULT_COUNTERPARTY_RPC_USER = "rpc"
DEFAULT_COUNTERPARTY_RPC_PASSWORD = "1234"


INITIAL_STATE = {
    "payer_wif": None,
    "payee_wif": None,
    "spend_secret": None,
    "deposit_script": None,
    "deposit_rawtx": None,
    "expire_rawtxs": [],  # ["rawtx", ...]
    "change_rawtxs": [],  # ["rawtx", ...]
    "revoke_rawtxs": [],  # ["rawtx", ...]
    "payout_rawtxs": [],  # ["rawtx", ...]

    # Quantity not needed as payer may change it. If its heigher its
    # against our self intrest to throw away money. If its lower it
    # gives us a better resolution when reversing the channel.
    "commits_requested": [],  # ["revoke_secret_hex"]

    # must be ordered lowest to heighest at all times!
    "commits_active": [],     # [{
    #                             "rawtx": hex,
    #                             "script": hex,
    #                             "revoke_secret": hex
    #                           }]

    "commits_revoked": [],    # [{
    #                            "rawtx": hex,  # unneeded?
    #                            "script": hex,
    #                            "revoke_secret": hex
    #                           }]
}


class Channel(object):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=DEFAULT_TESTNET, dryrun=False,
                 fee=DEFAULT_TXFEE, dust_size=DEFAULT_DUSTSIZE):
        # FIXME add doc string
        # FIXME validate all input
        if testnet:
            default_url = DEFAULT_COUNTERPARTY_RPC_TESTNET_URL
        else:
            default_url = DEFAULT_COUNTERPARTY_RPC_MAINNET_URL
        self.dryrun = dryrun
        self.fee = fee
        self.dust_size = dust_size
        self.api_url = api_url or default_url
        self.testnet = testnet
        self.user = user
        self.password = password
        self.asset = asset
        self.netcode = "BTC" if not self.testnet else "XTN"
        self.btctxstore = BtcTxStore(testnet=self.testnet, dryrun=dryrun,
                                     service="insight")
        self.bitcoind_rpc = AuthServiceProxy(  # XXX to publish
            "http://bitcoinrpcuser:bitcoinrpcpass@127.0.0.1:18332"
        )

    def setup(self, payee_wif):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        secret = os.urandom(32)  # secure random number
        state = copy.deepcopy(INITIAL_STATE)
        state["payee_wif"] = payee_wif
        state["spend_secret"] = util.b2h(secret)
        return {
            "channel_state": state,
            "payee_pubkey": util.wif2pubkey(state["payee_wif"]),
            "spend_secret_hash": util.b2h(util.hash160(secret))
        }

    def set_deposit(self, state, deposit):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        rawtx = deposit["rawtx"]
        script_hex = deposit["script"]
        self._validate_payer_deposit(rawtx, script_hex)
        script = util.h2b(script_hex)
        self._validate_deposit_spend_secret_hash(state, script)
        self._validate_deposit_payee_pubkey(state, script)
        state["deposit_rawtx"] = rawtx
        state["deposit_script"] = script_hex
        return {"channel_state": state}

    def request_commit(self, state, quantity):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        self._validate_transfer_quantity(state, quantity)
        secret = util.b2h(os.urandom(32))  # secure random number
        secret_hash = util.hash160hex(secret)
        state["commits_requested"].append(secret)
        return {
            "channel_state": state,
            "quantity": quantity,
            "revoke_secret_hash": secret_hash
        }

    def set_commit(self, state, rawtx, script_hex):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        self._validate_payer_commit(rawtx, script_hex)

        script = util.h2b(script_hex)
        self._validate_commit_secret_hash(state, script)
        self._validate_commit_payee_pubkey(state, script)

        revoke_secret_hash = get_commit_revoke_secret_hash(script)
        for revoke_secret in state["commits_requested"][:]:

            # revoke secret hash must match as it would
            # otherwise break the channels reversability
            if revoke_secret_hash == util.hash160hex(revoke_secret):

                # remove from requests
                state["commits_requested"].remove(revoke_secret)

                # add to active
                self._order_active(state)
                state["commits_active"].append({
                    "rawtx": rawtx, "script": script_hex,
                    "revoke_secret": revoke_secret
                })
                break
        return {"channel_state": state}

    def revoke_until(self, state, quantity):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        secrets = []
        self._order_active(state)
        for commit in reversed(state["commits_active"][:]):
            if quantity < self._get_quantity(commit["rawtx"]):
                secrets.append(commit["revoke_secret"])
            else:
                break
        list(map(lambda s: self._revoke(state, s), secrets))
        return {"channel_state": state, "revoke_secrets": secrets}

    def close_channel(self, state):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        assert(len(state["commits_active"]) > 0)
        self._order_active(state)
        commit = state["commits_active"][-1]

        # FIXME remove signing and publishing
        rawtx = scripts.sign_finalize_commit(
            self.btctxstore, state["payee_wif"],
            commit["rawtx"], state["deposit_script"]
        )
        commit["rawtx"] = rawtx  # update commit

        return {
            "channel_state": state,
            "topublish": {
                "rawtx": commit["rawtx"],
                "script": state["deposit_script"],
            }
        }

    def revoke_all(self, state, secrets):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        list(map(lambda s: self._revoke(state, s), secrets))
        return {"channel_state": state}

    def is_deposit_confirmed(self, state, minconfirms=1):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        validate.unsigned(minconfirms)
        script = util.h2b(state["deposit_script"])
        address = util.script2address(script, self.netcode)
        if self._get_address_balance(address) == (0, 0):
            return False
        rawtx = state["deposit_rawtx"]
        confirms = self.btctxstore.confirms(util.gettxid(rawtx)) or 0
        return confirms >= minconfirms

    def get_transferred_amount(self, state):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        if len(state["commits_active"]) == 0:
            return 0
        self._order_active(state)
        commit = state["commits_active"][-1]
        return self._get_quantity(commit["rawtx"])

    def create_commit(self, state, quantity, revoke_secret_hash, delay_time):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        self._validate_transfer_quantity(state, quantity)
        rawtx, commit_script = self._create_commit(
            state["payer_wif"], util.h2b(state["deposit_script"]),
            quantity, revoke_secret_hash, delay_time
        )

        # FIXME remove signing and publishing
        rawtx = scripts.sign_create_commit(
            self.btctxstore, state["payer_wif"],
            rawtx, state["deposit_script"]
        )

        commit_script_hex = util.b2h(commit_script)
        self._order_active(state)
        state["commits_active"].append({
            "rawtx": rawtx, "script": commit_script_hex, "revoke_secret": None
        })
        return {
            "channel_state": state,
            "commit_script": commit_script_hex,
            "tosign": {"rawtx": rawtx, "script": state["deposit_script"]}
        }

    def deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                expire_time, quantity):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        self._validate_deposit(payer_wif, payee_pubkey, spend_secret_hash,
                               expire_time, quantity)
        state = copy.deepcopy(INITIAL_STATE)
        state["payer_wif"] = payer_wif
        rawtx, script = self._deposit(
            state["payer_wif"], payee_pubkey,
            spend_secret_hash, expire_time, quantity
        )
        rawtx = self.btctxstore.sign_tx(rawtx, [state["payer_wif"]])
        state["deposit_rawtx"] = rawtx
        state["deposit_script"] = util.b2h(script)
        return {
            "channel_state": state,
            "deposit": {"rawtx": rawtx, "script": util.b2h(script)}
        }

    def payee_update(self, state):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        payouts = []

        # payout recoverable commits
        recoverable_scripts = self._get_payout_recoverable(state)
        if len(recoverable_scripts) > 0:
            for script in recoverable_scripts:
                rawtx = self._create_recover_commit(
                    state["payee_wif"], script, None,
                    state["spend_secret"], "payout"
                )
                payouts.append({
                    "rawtx": rawtx,
                    "script": util.b2h(script),
                    "secret": state["spend_secret"]
                })

                # FIXME remove signing and publishing
                rawtx = scripts.sign_payout_recover(
                    self.btctxstore, state["payee_wif"], rawtx,
                    util.b2h(script), state["spend_secret"]
                )

                state["payout_rawtxs"].append(rawtx)

        return {"channel_state": state, "payouts": payouts}

    def payer_update(self, state):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        topublish = {"revoke": [], "change": [], "expire": []}

        # If revoked commit published, recover funds asap!
        revokable = self._get_revoke_recoverable(state)
        if len(revokable) > 0:
            for script, secret in revokable:
                rawtx = self._create_recover_commit(
                    state["payer_wif"], script, secret, None, "revoke"
                )
                topublish["revoke"].append({
                    "rawtx": rawtx,
                    "script": util.b2h(script),
                    "secret": secret
                })

                # FIXME remove signing and publishing
                rawtx = scripts.sign_revoke_recover(
                    self.btctxstore, state["payer_wif"], rawtx,
                    util.b2h(script), secret
                )

                state["revoke_rawtxs"].append(rawtx)

        # If deposit expired recover the coins!
        if self._can_expire_recover(state):
            script = util.h2b(state["deposit_script"])
            rawtx = self._recover_deposit(state["payer_wif"],
                                          script, "expire", None)
            topublish["expire"].append({
                "rawtx": rawtx, "script": util.b2h(script)
            })

            # FIXME remove signing and publishing
            rawtx = scripts.sign_expire_recover(
                self.btctxstore, state["payer_wif"], rawtx, util.b2h(script)
            )

            state["expire_rawtxs"].append(rawtx)

        else:

            # If not expired and spend secret exposed by payout, recover
            # change!
            script = util.h2b(state["deposit_script"])
            address = util.script2address(script, self.netcode)
            if self._can_spend_from_address(address):
                spend_secret = self._find_spend_secret(state)
                if spend_secret is not None:
                    script = util.h2b(state["deposit_script"])
                    rawtx = self._recover_deposit(state["payer_wif"], script,
                                                  "change", spend_secret)
                    topublish["change"].append({
                        "rawtx": rawtx,
                        "script": util.b2h(script),
                        "secret": spend_secret
                    })

                    # FIXME remove signing and publishing
                    rawtx = scripts.sign_change_recover(
                        self.btctxstore, state["payer_wif"],
                        rawtx, util.b2h(script), spend_secret
                    )

                    state["change_rawtxs"].append(rawtx)

        return {"channel_state": state, "topublish": topublish}

    def payout_confirmed(self, state, minconfirms=1):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        validate.unsigned(minconfirms)
        return self._all_confirmed(state["payout_rawtxs"],
                                   minconfirms=minconfirms)

    def change_confirmed(self, state, minconfirms=1):
        # FIXME add doc string
        # FIXME validate all input
        # FIXME validate state
        state = copy.deepcopy(state)
        validate.unsigned(minconfirms)
        return self._all_confirmed(state["change_rawtxs"],
                                   minconfirms=minconfirms)

    def _rpc_call(self, payload):
        headers = {'content-type': 'application/json'}
        auth = HTTPBasicAuth(self.user, self.password)
        response = requests.post(self.api_url, data=json.dumps(payload),
                                 headers=headers, auth=auth)
        response_data = json.loads(response.text)
        if "result" not in response_data:
            raise Exception("Counterparty rpc call failed! {0}".format(
                repr(response.text)
            ))
        return response_data["result"]

    def _valid_channel_unused(self, channel_address):
        txs = self.btctxstore.get_transactions(channel_address)
        if len(txs) > 0:
            raise exceptions.ChannelAlreadyUsed(channel_address, txs)

    def _recover_tx(self, dest_address, script, sequence=None):

        # get channel info
        src_address = util.script2address(script, self.netcode)
        asset_balance, btc_balance = self._get_address_balance(src_address)

        # create expire tx
        rawtx = self._create_tx(src_address, dest_address, asset_balance,
                                extra_btc=btc_balance - self.fee)

        # prep for script compliance and signing
        tx = pycoin.tx.Tx.from_hex(rawtx)
        if sequence:
            tx.version = 2  # enable relative lock-time, see bip68 & bip112
        for txin in tx.txs_in:
            if sequence:
                txin.sequence = sequence  # relative lock-time
            utxo_tx = self.btctxstore.service.get_tx(txin.previous_hash)
            tx.unspents.append(utxo_tx.txs_out[txin.previous_index])

        rawtx = tx.as_hex()
        return rawtx

    def _create_recover_commit(self, wif, script, revoke_secret,
                               spend_secret, spend_type):

        dest_address = util.wif2address(wif)
        delay_time = get_commit_delay_time(script)
        return self._recover_tx(dest_address, script, delay_time)

    def _recover_deposit(self, wif, script, spend_type, spend_secret):
        dest_address = util.wif2address(wif)
        expire_time = get_deposit_expire_time(script)
        rawtx = self._recover_tx(
            dest_address, script,
            expire_time if spend_type == "expire" else None
        )
        return rawtx

    def _create_commit(self, payer_wif, deposit_script, quantity,
                       revoke_secret_hash, delay_time):

        # create script
        payer_pubkey = get_deposit_payer_pubkey(deposit_script)
        assert(util.wif2pubkey(payer_wif) == payer_pubkey)
        payee_pubkey = get_deposit_payee_pubkey(deposit_script)
        spend_secret_hash = get_deposit_spend_secret_hash(deposit_script)
        commit_script = compile_commit_script(
            payer_pubkey, payee_pubkey, spend_secret_hash,
            revoke_secret_hash, delay_time
        )

        # create tx
        src_address = util.script2address(deposit_script, self.netcode)
        dest_address = util.script2address(commit_script, self.netcode)
        asset_balance, btc_balance = self._get_address_balance(src_address)
        if quantity == asset_balance:  # spend all btc as change tx not needed
            extra_btc = btc_balance - self.fee
        else:  # provide extra btc for future payout/revoke tx fees
            extra_btc = (self.fee + self.dust_size)
        rawtx = self._create_tx(src_address, dest_address,
                                quantity, extra_btc=extra_btc)

        return rawtx, commit_script

    def _deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                 expire_time, quantity):

        payer_pubkey = util.wif2pubkey(payer_wif)
        script = compile_deposit_script(payer_pubkey, payee_pubkey,
                                        spend_secret_hash, expire_time)
        dest_address = util.script2address(script, self.netcode)
        self._valid_channel_unused(dest_address)
        payer_address = util.wif2address(payer_wif)

        # provide extra btc for future closing channel fees
        # change tx or recover + commit tx + payout tx or revoke tx
        extra_btc = (self.fee + self.dust_size) * 3

        rawtx = self._create_tx(payer_address, dest_address,
                                quantity, extra_btc=extra_btc)
        return rawtx, script

    def _create_tx(self, source_address, dest_address, quantity, extra_btc=0):
        assert(extra_btc >= 0)
        rawtx = self._rpc_call({
            "method": "create_send",
            "params": {
                "source": source_address,
                "destination": dest_address,
                "quantity": quantity,
                "asset": self.asset,
                "regular_dust_size": extra_btc or self.dust_size,
                "fee": self.fee
            },
            "jsonrpc": "2.0",
            "id": 0,
        })
        assert(self._get_quantity(rawtx) == quantity)
        return rawtx

    def _can_spend_from_address(self, address):

        # has assets, btc
        if self._get_address_balance(address) == (0, 0):
            return False

        # TODO check if btc > fee

        # can only spend if all txs confirmed
        txids = self.btctxstore.get_transactions(address)
        latest_confirms = self.btctxstore.confirms(txids[0])
        return latest_confirms > 0

    def _get_address_balance(self, address):
        result = self._rpc_call({
            "method": "get_balances",
            "params": {
                "filters": [
                    {'field': 'address', 'op': '==', 'value': address},
                    {'field': 'asset', 'op': '==', 'value': self.asset},
                ]
            },
            "jsonrpc": "2.0",
            "id": 0,
        })
        if not result:  # FIXME what causes this?
            return 0, 0
        asset_balance = result[0]["quantity"]
        utxos = self.btctxstore.retrieve_utxos([address])
        btc_balance = sum(map(lambda utxo: utxo["value"], utxos))
        return asset_balance, btc_balance

    def publish(self, rawtx):
        txid = util.gettxid(rawtx)
        if self.dryrun:
            return txid
        while self.btctxstore.confirms(util.gettxid(rawtx)) is None:
            try:
                self.bitcoind_rpc.sendrawtransaction(rawtx)
                return util.gettxid(rawtx)
                # see http://counterparty.io/docs/api/#wallet-integration
            except Exception as e:
                print("publishing failed: {0} {1}".format(type(e), e))
            time.sleep(10)

    def _get_quantity(self, rawtx):
        result = self._rpc_call({
            "method": "get_tx_info",
            "params": {
                "tx_hex": rawtx
            },
            "jsonrpc": "2.0",
            "id": 0,
        })
        src, dest, btc, fee, data = result
        result = self._rpc_call({
            "method": "unpack",
            "params": {
                "data_hex": data
            },
            "jsonrpc": "2.0",
            "id": 0,
        })
        message_type_id, unpacked = result
        if message_type_id != 0:
            msg = "Incorrect message type id: {0} != {1}"
            raise ValueError(msg.format(message_type_id, 0))
        if self.asset != unpacked["asset"]:
            msg = "Incorrect asset: {0} != {1}"
            raise ValueError(msg.format(self.asset, unpacked["asset"]))
        return unpacked["quantity"]

    def _validate_transfer_quantity(self, state, quantity):
        transferred = self.get_transferred_amount(state)
        if quantity <= transferred:
            msg = "Amount not greater transferred: {0} <= {1}"
            raise ValueError(msg.format(quantity, transferred))

        total = self._get_quantity(state["deposit_rawtx"])
        if quantity > total:
            msg = "Amount greater total: {0} > {1}"
            raise ValueError(msg.fromat(quantity, total))

    def _order_active(self, state):

        def sort_func(entry):
            return self._get_quantity(entry["rawtx"])
        state["commits_active"].sort(key=sort_func)

    def _revoke(self, state, secret):
        secret_hash = util.hash160hex(secret)
        for commit in state["commits_active"][:]:
            script = util.h2b(commit["script"])
            if secret_hash == get_commit_revoke_secret_hash(script):
                state["commits_active"].remove(commit)
                commit["revoke_secret"] = secret  # save secret
                state["commits_revoked"].append(commit)

    def _all_confirmed(self, rawtxs, minconfirms=1):
        validate.unsigned(minconfirms)
        if len(rawtxs) == 0:
            return False
        for rawtx in rawtxs:
            confirms = self.btctxstore.confirms(util.gettxid(rawtx)) or 0
            if confirms < minconfirms:
                return False
        return True

    def _commit_spent(self, state, commit):
        txid = util.gettxid(commit["rawtx"])
        for rawtx in (state["payout_rawtxs"] + state["revoke_rawtxs"] +
                      state["change_rawtxs"] + state["expire_rawtxs"]):
            tx = pycoin.tx.Tx.from_hex(rawtx)
            for txin in tx.txs_in:
                if util.b2h_rev(txin.previous_hash) == txid:
                    return True
        return False

    def _validate_deposit_spend_secret_hash(self, state, script):
        given_spend_secret_hash = get_deposit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(state["spend_secret"])
        if given_spend_secret_hash != own_spend_secret_hash:
            msg = "Incorrect spend secret hash: {0} != {1}"
            raise ValueError(msg.format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

    def _validate_deposit_payee_pubkey(self, state, script):
        given_payee_pubkey = get_deposit_payee_pubkey(script)
        own_payee_pubkey = util.wif2pubkey(state["payee_wif"])
        if given_payee_pubkey != own_payee_pubkey:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, own_payee_pubkey
            ))

    def _validate_payer_deposit(self, rawtx, script_hex):
        tx = pycoin.tx.Tx.from_hex(rawtx)
        assert(tx.bad_signature_count() == 1)

        # TODO validate script
        # TODO check given script and rawtx match
        # TODO check given script is deposit script

    def _validate_payer_commit(self, rawtx, script_hex):
        tx = pycoin.tx.Tx.from_hex(rawtx)
        assert(tx.bad_signature_count() == 1)

        # TODO validate script
        # TODO validate rawtx signed by payer
        # TODO check it is for the current deposit
        # TODO check given script and rawtx match
        # TODO check given script is commit script

    def _validate_commit_secret_hash(self, state, script):
        given_spend_secret_hash = get_commit_spend_secret_hash(script)
        own_spend_secret_hash = util.hash160hex(state["spend_secret"])
        if given_spend_secret_hash != own_spend_secret_hash:
            msg = "Incorrect spend secret hash: {0} != {1}"
            raise ValueError(msg.format(
                given_spend_secret_hash, own_spend_secret_hash
            ))

    def _validate_commit_payee_pubkey(self, state, script):
        given_payee_pubkey = get_commit_payee_pubkey(script)
        own_payee_pubkey = util.wif2pubkey(state["payee_wif"])
        if given_payee_pubkey != own_payee_pubkey:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, own_payee_pubkey
            ))

    def _get_payout_recoverable(self, state):
        scripts = []
        for commit in (state["commits_active"] +
                       state["commits_revoked"]):
            script = util.h2b(commit["script"])
            delay_time = get_commit_delay_time(script)
            address = util.script2address(
                script, netcode=self.netcode
            )
            if self._commit_spent(state, commit):
                continue
            if self._can_spend_from_address(address):
                utxos = self.btctxstore.retrieve_utxos([address])
                for utxo in utxos:
                    txid = utxo["txid"]
                    confirms = self.btctxstore.confirms(txid)
                    if confirms >= delay_time:
                        scripts.append(script)
        return scripts

    def _can_expire_recover(self, state):
        return (
            # we know the payer wif
            state["payer_wif"] is not None and

            # deposit was made
            state["deposit_rawtx"] is not None and
            state["deposit_script"] is not None and

            # deposit expired
            self._is_deposit_expired(state) and

            # funds to recover
            self._can_deposit_spend(state)
        )

    def _can_deposit_spend(self, state):
        script = util.h2b(state["deposit_script"])
        address = util.script2address(script, self.netcode)
        return self._can_spend_from_address(address)

    def _is_deposit_expired(self, state):
        script = util.h2b(state["deposit_script"])
        t = get_deposit_expire_time(script)
        rawtx = state["deposit_rawtx"]
        confirms = self.btctxstore.confirms(util.gettxid(rawtx)) or 0
        return confirms >= t

    def _validate_deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                          expire_time, quantity):

        # validate untrusted input data
        validate.wif(payer_wif, self.netcode)
        validate.pubkey(payee_pubkey)
        validate.hash160(spend_secret_hash)
        validate.sequence(expire_time)
        validate.quantity(quantity)

        # get balances
        address = util.wif2address(payer_wif)
        asset_balance, btc_balance = self._get_address_balance(address)

        # check asset balance
        if asset_balance < quantity:
            raise exceptions.InsufficientFunds(quantity, asset_balance)

        # check btc balance
        extra_btc = (self.fee + self.dust_size) * 3
        if btc_balance < extra_btc:
            raise exceptions.InsufficientFunds(extra_btc, btc_balance)

    def _find_spend_secret(self, state):
        for commit in state["commits_active"] + \
                state["commits_revoked"]:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.netcode
            )
            txs = self.btctxstore.get_transactions(address)
            if len(txs) == 1:
                continue  # only the commit, no payout
            for txid in txs:
                rawtx = self.btctxstore.retrieve_tx(txid)
                spend_secret = scripts.get_spend_secret(rawtx, script)
                if spend_secret is not None:
                    return spend_secret
        return None

    def _get_revoke_recoverable(self, state):
        commits_revoked = state["commits_revoked"]
        revokable = []  # (script, secret)
        for commit in commits_revoked:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.netcode
            )
            if self._can_spend_from_address(address):
                revokable.append((script, commit["revoke_secret"]))
        return revokable
