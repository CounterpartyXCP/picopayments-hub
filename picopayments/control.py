# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import six
import pycoin
import json
import requests
from btctxstore import BtcTxStore
from requests.auth import HTTPBasicAuth
from . import util
from . import scripts
from . import exceptions


# FIXME make fees per kb and auto adjust to market price
DEFAULT_TXFEE = 10000  # FIXME dont hardcode tx fee
DEFAULT_DUSTSIZE = 5430  # FIXME dont hardcode dust size
DEFAULT_TESTNET = False
DEFAULT_COUNTERPARTY_RPC_MAINNET_URL = "http://public.coindaddy.io:4000/api/"
DEFAULT_COUNTERPARTY_RPC_TESTNET_URL = "http://public.coindaddy.io:14000/api/"
DEFAULT_COUNTERPARTY_RPC_USER = "rpc"
DEFAULT_COUNTERPARTY_RPC_PASSWORD = "1234"


class Control(object):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 api_url=None, testnet=DEFAULT_TESTNET, dryrun=False,
                 fee=DEFAULT_TXFEE, dust_size=DEFAULT_DUSTSIZE):
        """Initialize payment channel controler.

        Args:
            asset (str): Counterparty asset name.
            user (str): Counterparty API username.
            password (str): Counterparty API password.
            api_url (str): Counterparty API url.
            testnet (bool): True if running on testnet, otherwise mainnet.
            dryrun (bool): If True nothing will be published to the blockchain.
            fee (int): The transaction fee to use.
            dust_size (int): The default dust size for counterparty outputs.
        """

        if testnet:
            default_url = DEFAULT_COUNTERPARTY_RPC_TESTNET_URL
        else:
            default_url = DEFAULT_COUNTERPARTY_RPC_MAINNET_URL

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

    def create_tx(self, source_address, dest_address, quantity, extra_btc=0):
        assert(extra_btc >= 0)
        return self._rpc_call({
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

    def get_balance(self, address):
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
        asset_balance = result[0]["quantity"]
        utxos = self.btctxstore.retrieve_utxos([address])
        btc_balance = sum(map(lambda utxo: utxo["value"], utxos))
        return asset_balance, btc_balance

    def _valid_deposit_request(self, payer_wif, payee_pubkey,
                               spend_secret_hash, expire_time, quantity):

        # FIXME validate channel previously unused

        # quantity must be > 0
        if not isinstance(quantity, six.integer_types) or quantity <= 0:
            raise ValueError()

        # get balances
        address = util.wif2address(payer_wif)
        asset_balance, btc_balance = self.get_balance(address)

        # check asset balance
        if asset_balance < quantity:
            raise InsufficientFunds(quantity, asset_balance)

        # check btc balance
        extra_btc = (self.fee + self.dust_size) * 3
        if btc_balance < extra_btc:
            raise InsufficientFunds(extra_btc, btc_balance)

    def deposit(self, payer_wif, payee_pubkey, spend_secret_hash,
                expire_time, quantity):

        self._valid_deposit_request(payer_wif, payee_pubkey, spend_secret_hash,
                                    expire_time, quantity)

        payer_pubkey = util.wif2pubkey(payer_wif)
        script = scripts.compile_deposit_script(payer_pubkey, payee_pubkey,
                                                spend_secret_hash, expire_time)
        dest_address = util.script2address(script, self.netcode)
        payer_address = util.wif2address(payer_wif)

        # provide extra btc for future closing channel fees
        # change tx or recover + commit tx + payout tx or revoke tx
        extra_btc = (self.fee + self.dust_size) * 3

        rawtx = self.create_tx(payer_address, dest_address,
                               quantity, extra_btc=extra_btc)
        rawtx = self.btctxstore.sign_tx(rawtx, [payer_wif])
        self.btctxstore.publish(rawtx)
        return rawtx, script, dest_address

    def _recover(self, payer_wif, deposit_rawtx,
                 script, spend_type, spend_secret):

        # get channel info
        channel_address = util.script2address(script, self.netcode)
        asset_balance, btc_balance = self.get_balance(channel_address)
        expire_time = scripts.get_deposit_expire_time(script)

        # create timeout tx
        payer_address = util.wif2address(payer_wif)
        rawtx = self.create_tx(channel_address, payer_address, asset_balance,
                               extra_btc=btc_balance-self.fee)

        # prep for script compliance and signing
        tx = pycoin.tx.Tx.from_hex(rawtx)
        if spend_type == "timeout":
            tx.version = 2  # enable relative lock-time, see bip68 & bip112
        for txin in tx.txs_in:
            if spend_type == "timeout":
                txin.sequence = expire_time  # relative lock-time
            utxo_tx = self.btctxstore.service.get_tx(txin.previous_hash)
            tx.unspents.append(utxo_tx.txs_out[txin.previous_index])

        # sign
        hash160_lookup = pycoin.tx.pay_to.build_hash160_lookup(
            [util.wif2secretexponent(payer_wif)]
        )
        p2sh_lookup = pycoin.tx.pay_to.build_p2sh_lookup([script])
        with scripts.DepositScriptHandler(expire_time):
            tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup,
                    spend_type=spend_type, spend_secret=spend_secret)

        # FIXME patch pycoin so it works
        # assert(tx.bad_signature_count() == 0)

        rawtx = tx.as_hex()
        self.btctxstore.publish(rawtx)
        return rawtx

    def timeout_recover(self, payer_wif, deposit_rawtx, script):
        return self._recover(payer_wif, deposit_rawtx, script, "timeout", None)

    def change_recover(self, payer_wif, deposit_rawtx, script, spend_secret):
        return self._recover(payer_wif, deposit_rawtx,
                             script, "change", spend_secret)
