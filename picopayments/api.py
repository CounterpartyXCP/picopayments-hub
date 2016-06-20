# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import time
import json
import requests
from btctxstore import BtcTxStore
from requests.auth import HTTPBasicAuth
from bitcoinrpc.authproxy import AuthServiceProxy
from picopayments import util


DEFAULT_TESTNET = False
DEFAULT_COUNTERPARTY_RPC_MAINNET_URL = "http://public.coindaddy.io:4000/api/"
DEFAULT_COUNTERPARTY_RPC_TESTNET_URL = "http://public.coindaddy.io:14000/api/"
DEFAULT_COUNTERPARTY_RPC_USER = "rpc"
DEFAULT_COUNTERPARTY_RPC_PASSWORD = "1234"


class Api(object):

    def __init__(self, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD,
                 url=None, testnet=DEFAULT_TESTNET, dryrun=False):
        if testnet:
            default_url = DEFAULT_COUNTERPARTY_RPC_TESTNET_URL
        else:
            default_url = DEFAULT_COUNTERPARTY_RPC_MAINNET_URL
        self.dryrun = dryrun
        self.url = url or default_url
        self.user = user
        self.password = password
        self.btctxstore = BtcTxStore(
            testnet=testnet, dryrun=dryrun, service="insight"
        )
        self.bitcoind_rpc = AuthServiceProxy(  # XXX to publish
            "http://bitcoinrpcuser:bitcoinrpcpass@127.0.0.1:18332"
        )

    def call(self, method, params):
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": 0
        }
        headers = {'content-type': 'application/json'}
        auth = HTTPBasicAuth(self.user, self.password)
        response = requests.post(self.url, data=json.dumps(payload),
                                 headers=headers, auth=auth)
        response_data = json.loads(response.text)
        if "result" not in response_data:
            print(json.dumps(payload, indent=2))
            raise Exception("Counterparty rpc call failed! {0}".format(
                repr(response.text)
            ))
        return response_data["result"]

    def publish(self, rawtx):
        # FIXME remove this
        if self.dryrun:
            return util.gettxid(rawtx)
        while self.btctxstore.confirms(util.gettxid(rawtx)) is None:
            try:
                self.bitcoind_rpc.sendrawtransaction(rawtx)
                return util.gettxid(rawtx)
                # see http://counterparty.io/docs/api/#wallet-integration
            except Exception as e:
                print("publishing failed: {0} {1}".format(type(e), e))
            time.sleep(10)
