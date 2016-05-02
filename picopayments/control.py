# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import pycoin
import json
import requests
from btctxstore import BtcTxStore
from requests.auth import HTTPBasicAuth
from . import scripts


DEFAULT_TESTNET = False
DEFAULT_COUNTERPARTY_RPC_MAINNET_URL = "http://public.coindaddy.io:4000/api/"
DEFAULT_COUNTERPARTY_RPC_TESTNET_URL = "http://public.coindaddy.io:14000/api/"
DEFAULT_COUNTERPARTY_RPC_USER = "rpc"
DEFAULT_COUNTERPARTY_RPC_PASSWORD = "1234"


class Control(object):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD, counterparty_url=None,
                 testnet=DEFAULT_TESTNET, dryrun=False):

        if testnet:
            self.counterparty_url = DEFAULT_COUNTERPARTY_RPC_TESTNET_URL
        else:
            self.counterparty_url = DEFAULT_COUNTERPARTY_RPC_MAINNET_URL
        self.testnet = testnet
        self.user = user
        self.password = password
        self.asset = asset
        self.netcode = "BTC" if not self.testnet else "XTN"
        self.btctxstore = BtcTxStore(testnet=self.testnet, dryrun=dryrun)

    def _rpc_call(self, payload):
        headers = {'content-type': 'application/json'}
        auth = HTTPBasicAuth(self.user, self.password)
        response = requests.post(self.counterparty_url, data=json.dumps(payload),
                                 headers=headers, auth=auth)
        response_data = json.loads(response.text)
        if "result" not in response_data:
            raise Exception("Counterparty rpc call failed! {0}".format(
                repr(response)
            ))
        return response_data["result"]

    def _create_tx(self, source_address, dest_address, quantity):
        return self._rpc_call({
            "method": "create_send",
            "params": {
                "source": source_address,
                "destination": dest_address,
                "quantity": quantity,
                "asset": self.asset,
                # TODO "regular_dust_size" to ensur enough btc for refund fee
            },
            "jsonrpc": "2.0",
            "id": 0,
        })

    def get_balance(self, address):
        return self._rpc_call({
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

    def deposit(self, payer_wif, payee_sec, quantity,
                expire_time, recover_sec=None):
        payer_sec = wif2sec(payer_wif)
        recover_sec = recover_sec or payer_sec
        script = script.create_deposit_script(payer_sec, payee_sec,
                                              recover_sec, expire_time)
        dest_address = script2address(script, self.netcode)
        payer_address = wif2address(payer_wif)
        rawtx = self._create_tx(payer_address, dest_address, quantity)
        signed_rawtx = self.btctxstore.sign_tx(rawtx, [payer_wif])
        return signed_rawtx, script

    def recover(self, recover_wif, script, quantity, expire_time):
        # TODO remove quantity and send all assets to recover address
        # TODO get expire_time from script

        # create recover tx
        channel_address = script2address(script, self.netcode)
        recover_address = wif2address(recover_wif)
        rawtx = self._create_tx(channel_address, recover_address, quantity)

        # prep for script compliance and signing
        tx = pycoin.tx.Tx.from_hex(rawtx)
        tx.version = 2  # enable relative lock-time, see bip68 & bip112
        for txin in tx.txs_in:
            txin.sequence = expire_time
            utxo_tx = self.btctxstore.service.get_tx(txin.previous_hash)
            tx.unspents.append(utxo_tx.txs_out[txin.previous_index])

        # sign
        secret_exponent = wif2secretexponent(recover_wif)
        hash160_lookup = pycoin.tx.pay_to.build_hash160_lookup(
            [secret_exponent]
        )
        p2sh_lookup = pycoin.tx.pay_to.build_p2sh_lookup([script])
        tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup)

        assert(tx.bad_signature_count() == 0)
        return tx.as_hex()
