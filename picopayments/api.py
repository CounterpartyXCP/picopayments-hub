# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import copy
import pycoin
import time
import json
import requests
from btctxstore import BtcTxStore
from requests.auth import HTTPBasicAuth
from bitcoinrpc.authproxy import AuthServiceProxy
from picopayments import util
from picopayments import validate
from picopayments.scripts import get_deposit_spend_secret_hash
from picopayments.scripts import get_commit_revoke_secret_hash
from picopayments import exceptions
from picopayments import scripts


# TODO fees per kb, auto adjust to market price or get from counterparty
DEFAULT_TXFEE = 10000  # TODO dont hardcode tx fee
DEFAULT_DUSTSIZE = 5430  # TODO dont hardcode dust size
DEFAULT_TESTNET = False
DEFAULT_COUNTERPARTY_RPC_MAINNET_URL = "http://public.coindaddy.io:4000/api/"
DEFAULT_COUNTERPARTY_RPC_TESTNET_URL = "http://public.coindaddy.io:14000/api/"
DEFAULT_COUNTERPARTY_RPC_USER = "rpc"
DEFAULT_COUNTERPARTY_RPC_PASSWORD = "1234"


INITIAL_STATE = {
    "payee_pubkey": None,
    "deposit_script": None,

    # Quantity not needed as payer may change it. If its heigher its
    # against our self intrest to throw away money. If its lower it
    # gives us a better resolution when reversing the channel.
    "commits_requested": [],  # ["revoke_secret_hash"]

    # must be ordered lowest to heighest at all times!
    "commits_active": [],     # [{
    #                             "rawtx": hex,
    #                             "script": hex,
    #                           }]

    "commits_revoked": [],    # [{
    #                             "script": hex,
    #                             "revoke_secret": hex
    #                           }]
}


class Api(object):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=DEFAULT_TESTNET, dryrun=False,
                 fee=DEFAULT_TXFEE, dust_size=DEFAULT_DUSTSIZE):
        # TODO add doc string
        # TODO validate all input
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
        self.btctxstore = BtcTxStore(
            testnet=self.testnet, dryrun=dryrun, service="insight"
        )
        self.bitcoind_rpc = AuthServiceProxy(  # XXX to publish
            "http://bitcoinrpcuser:bitcoinrpcpass@127.0.0.1:18332"
        )

    def payee_setup(self, payee_pubkey, spend_secret_hash):
        """Setup payment channel.

        Args:
            payee_pubkey: Payee hex encoded public key in sec format.
            spend_secret_hash: Hex encoded hash160 of spend secret.

        Returns:
            {
                "payee_state": state,
                "payee_pubkey": payee_pubkey,
                "spend_secret_hash": hex_encoded_secret_hash
            }

        Raises:
            picopayments.exceptions.InvalidPubKey
            picopayments.exceptions.InvalidHash160
        """
        validate.pubkey(payee_pubkey)
        validate.hash160(spend_secret_hash)
        state = copy.deepcopy(INITIAL_STATE)
        state["payee_pubkey"] = payee_pubkey
        return {
            "payee_state": state,
            "payee_pubkey": payee_pubkey,
            "spend_secret_hash": spend_secret_hash
        }

    def set_deposit(self, state, deposit_script):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        script_bin = util.h2b(deposit_script)
        self._validate_deposit_payee_pubkey(state, script_bin)
        state["deposit_script"] = deposit_script
        return {"state": state}

    def request_commit(self, state, quantity, secret_hash):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        self._validate_transfer_quantity(state, quantity)
        state["commits_requested"].append(secret_hash)
        return {
            "state": state,
            "quantity": quantity,
            "revoke_secret_hash": secret_hash
        }

    def set_commit(self, state, rawtx, commit_script):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        self._validate_payer_commit(rawtx, commit_script)

        script_bin = util.h2b(commit_script)
        self._validate_commit_payee_pubkey(state, script_bin)

        script_revoke_secret_hash = get_commit_revoke_secret_hash(script_bin)
        for revoke_secret_hash in state["commits_requested"][:]:

            # revoke secret hash must match as it would
            # otherwise break the channels reversability
            if script_revoke_secret_hash == revoke_secret_hash:

                # remove from requests
                state["commits_requested"].remove(revoke_secret_hash)

                # add to active
                self._order_active(state)
                state["commits_active"].append({
                    "rawtx": rawtx,
                    "script": commit_script
                })
                break
        return {"state": state}

    def revoke_secret_hashes_until(self, state, quantity):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        revoke_secret_hashes = []
        self._order_active(state)
        for commit in reversed(state["commits_active"][:]):
            if quantity < self._get_quantity(commit["rawtx"]):
                script = util.h2b(commit["script"])
                secret_hash = get_commit_revoke_secret_hash(script)
                revoke_secret_hashes.append(secret_hash)
            else:
                break
        return revoke_secret_hashes

    def close_channel(self, state):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        assert(len(state["commits_active"]) > 0)
        self._order_active(state)
        commit = state["commits_active"][-1]
        return {
            "state": state,
            "topublish": {
                "rawtx": commit["rawtx"],
                "deposit_script": state["deposit_script"],
            }
        }

    def revoke_all(self, state, secrets):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        list(map(lambda s: self._revoke(state, s), secrets))
        return {"state": state}

    def is_deposit_confirmed(self, state, minconfirms=1):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        validate.unsigned(minconfirms)
        script = util.h2b(state["deposit_script"])
        confirms, asset_balance, btc_balance = self._deposit_status(script)
        return confirms >= minconfirms

    def get_transferred_amount(self, state):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        if len(state["commits_active"]) == 0:
            return 0
        self._order_active(state)
        commit = state["commits_active"][-1]
        return self._get_quantity(commit["rawtx"])

    def create_commit(self, state, quantity, revoke_secret_hash, delay_time):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        self._validate_transfer_quantity(state, quantity)
        deposit_script = util.h2b(state["deposit_script"])
        rawtx, commit_script = self._create_commit(
            deposit_script, quantity, revoke_secret_hash, delay_time
        )

        commit_script_hex = util.b2h(commit_script)
        self._order_active(state)
        state["commits_active"].append({
            "rawtx": rawtx, "script": commit_script_hex
        })
        return {
            "state": state,
            "commit_script": commit_script_hex,
            "tosign": {
                "rawtx": rawtx, "deposit_script": state["deposit_script"]
            }
        }

    def deposit(self, payer_pubkey, payee_pubkey, spend_secret_hash,
                expire_time, quantity):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        self._validate_deposit(payer_pubkey, payee_pubkey, spend_secret_hash,
                               expire_time, quantity)
        state = copy.deepcopy(INITIAL_STATE)
        rawtx, script = self._deposit(
            payer_pubkey, payee_pubkey,
            spend_secret_hash, expire_time, quantity
        )
        state["deposit_script"] = util.b2h(script)
        return {
            "state": state,
            "topublish": rawtx,
            "deposit_script": util.b2h(script)
        }

    def payee_update(self, state):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        payouts = []

        # payout recoverable commits
        recoverable_scripts = self._get_payout_recoverable(state)
        if len(recoverable_scripts) > 0:
            for script in recoverable_scripts:
                rawtx = self._create_recover_commit(
                    state["payee_pubkey"], script, "payout"
                )
                payouts.append({
                    "rawtx": rawtx, "commit_script": util.b2h(script)
                })
        return {"state": state, "payouts": payouts}

    def payer_update(self, state):
        # TODO add doc string
        # TODO validate all input
        # TODO validate state
        state = copy.deepcopy(state)
        deposit_script = util.h2b(state["deposit_script"])
        payer_pubkey = scripts.get_deposit_payer_pubkey(deposit_script)
        topublish = {"revoke": [], "change": [], "expire": []}

        # If revoked commit published, recover funds asap!
        revokable = self._get_revoke_recoverable(state)
        if len(revokable) > 0:
            for script, secret in revokable:
                rawtx = self._create_recover_commit(
                    payer_pubkey, script, "revoke"
                )
                topublish["revoke"].append({
                    "rawtx": rawtx,
                    "commit_script": util.b2h(script),
                    "revoke_secret": secret
                })

        # If deposit expired recover the coins!
        if self._can_expire_recover(state):
            rawtx = self._recover_deposit(
                payer_pubkey, deposit_script, "expire")
            topublish["expire"].append({
                "rawtx": rawtx, "deposit_script": state["deposit_script"]
            })

        else:

            # If not expired and spend secret exposed by payout
            # recover change!
            address = util.script2address(deposit_script, self.netcode)
            if self._can_spend_from_address(address):
                _spend_secret = self._find_spend_secret(state)
                if _spend_secret is not None:
                    rawtx = self._recover_deposit(
                        payer_pubkey, deposit_script, "change"
                    )
                    topublish["change"].append({
                        "rawtx": rawtx,
                        "deposit_script": state["deposit_script"],
                        "spend_secret": _spend_secret
                    })

        return {"state": state, "topublish": topublish}

    def publish(self, rawtx):
        # TODO remove this
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

    def _deposit_status(self, script):
        address = util.script2address(script, self.netcode)
        txids = self.btctxstore.get_transactions(address)
        if len(txids) == 0:
            return 0, 0, 0
        asset_balance, btc_balance = self._get_address_balance(address)
        newest_confirms = self.btctxstore.confirms(txids[0]) or 0
        oldest_confirms = self.btctxstore.confirms(txids[-1]) or 0
        if newest_confirms == 0:
            return 0, asset_balance, btc_balance
        return oldest_confirms, asset_balance, btc_balance

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

    def _create_recover_commit(self, pubkey, script, spend_type):
        dest_address = util.pubkey2address(pubkey, netcode=self.netcode)
        delay_time = scripts.get_commit_delay_time(script)
        return self._recover_tx(dest_address, script, delay_time)

    def _recover_deposit(self, pubkey, script, spend_type):
        dest_address = util.pubkey2address(pubkey, netcode=self.netcode)
        expire_time = scripts.get_deposit_expire_time(script)
        rawtx = self._recover_tx(
            dest_address, script,
            expire_time if spend_type == "expire" else None
        )
        return rawtx

    def _create_commit(self, deposit_script, quantity,
                       revoke_secret_hash, delay_time):

        # create script
        payer_pubkey = scripts.get_deposit_payer_pubkey(deposit_script)
        payee_pubkey = scripts.get_deposit_payee_pubkey(deposit_script)
        spend_secret_hash = get_deposit_spend_secret_hash(deposit_script)
        commit_script = scripts.compile_commit_script(
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

    def _deposit(self, payer_pubkey, payee_pubkey, spend_secret_hash,
                 expire_time, quantity):

        script = scripts.compile_deposit_script(payer_pubkey, payee_pubkey,
                                                spend_secret_hash, expire_time)
        dest_address = util.script2address(script, self.netcode)
        self._valid_channel_unused(dest_address)
        payer_address = util.pubkey2address(payer_pubkey, self.netcode)

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
        if not result:  # TODO what causes this?
            return 0, 0
        asset_balance = result[0]["quantity"]
        utxos = self.btctxstore.retrieve_utxos([address])
        btc_balance = sum(map(lambda utxo: utxo["value"], utxos))
        return asset_balance, btc_balance

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
        script = util.h2b(state["deposit_script"])
        confirms, asset_balance, btc_balance = self._deposit_status(script)
        if quantity > asset_balance:
            msg = "Amount greater total: {0} > {1}"
            raise ValueError(msg.fromat(quantity, asset_balance))

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
                del commit["rawtx"]  # forget rawtx so we can never publish
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

    def _validate_deposit_payee_pubkey(self, state, script):
        given_payee_pubkey = scripts.get_deposit_payee_pubkey(script)
        if given_payee_pubkey != state["payee_pubkey"]:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, state["payee_pubkey"]
            ))

    def _validate_commit_payee_pubkey(self, state, script):
        given_payee_pubkey = scripts.get_commit_payee_pubkey(script)
        if given_payee_pubkey != state["payee_pubkey"]:
            msg = "Incorrect payee pubkey: {0} != {1}"
            raise ValueError(msg.format(
                given_payee_pubkey, state["payee_pubkey"]
            ))

    def _validate_payer_commit(self, rawtx, script_hex):
        tx = pycoin.tx.Tx.from_hex(rawtx)
        assert(tx.bad_signature_count() == 1)

        # TODO validate script
        # TODO validate rawtx signed by payer
        # TODO check it is for the current deposit
        # TODO check given script and rawtx match
        # TODO check given script is commit script

    def _get_payout_recoverable(self, state):
        _scripts = []
        for commit in (state["commits_active"] + state["commits_revoked"]):
            script = util.h2b(commit["script"])
            delay_time = scripts.get_commit_delay_time(script)
            address = util.script2address(script, netcode=self.netcode)
            if self._can_spend_from_address(address):
                utxos = self.btctxstore.retrieve_utxos([address])
                for utxo in utxos:
                    txid = utxo["txid"]
                    confirms = self.btctxstore.confirms(txid)
                    if confirms >= delay_time:
                        _scripts.append(script)
        return _scripts

    def _can_expire_recover(self, state):
        return (
            # deposit was made
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
        t = scripts.get_deposit_expire_time(script)
        confirms, asset_balance, btc_balance = self._deposit_status(script)
        return confirms >= t

    def _validate_deposit(self, payer_pubkey, payee_pubkey, spend_secret_hash,
                          expire_time, quantity):

        # validate untrusted input data
        validate.pubkey(payer_pubkey)
        validate.pubkey(payee_pubkey)
        validate.hash160(spend_secret_hash)
        validate.sequence(expire_time)
        validate.quantity(quantity)

        # get balances
        address = util.pubkey2address(payer_pubkey, self.netcode)
        asset_balance, btc_balance = self._get_address_balance(address)

        # check asset balance
        if asset_balance < quantity:
            raise exceptions.InsufficientFunds(quantity, asset_balance)

        # check btc balance
        extra_btc = (self.fee + self.dust_size) * 3
        if btc_balance < extra_btc:
            raise exceptions.InsufficientFunds(extra_btc, btc_balance)

    def _find_spend_secret(self, state):
        for commit in state["commits_active"] + state["commits_revoked"]:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.netcode
            )
            txs = self.btctxstore.get_transactions(address)
            if len(txs) == 1:
                continue  # only the commit, no payout
            for txid in txs:
                rawtx = self.btctxstore.retrieve_tx(txid)
                _spend_secret = scripts.get_spend_secret(rawtx, script)
                if _spend_secret is not None:
                    return _spend_secret
        return None

    def _get_revoke_recoverable(self, state):
        revokable = []  # (script, secret)
        for commit in state["commits_revoked"]:
            script = util.h2b(commit["script"])
            address = util.script2address(
                script, netcode=self.netcode
            )
            if self._can_spend_from_address(address):
                revokable.append((script, commit["revoke_secret"]))
        return revokable
