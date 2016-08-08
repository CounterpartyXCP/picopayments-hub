import os
import time
import jsonschema
import shutil
import unittest
import tempfile
from counterpartylib.lib.micropayments import util
from picopayments import control
from picopayments import exceptions
from picopayments.main import main
from multiprocessing import Process
from picopayments import rpc


HOST = "127.0.0.1"
PORT = "15000"
URL = "https://127.0.0.1:15000/api/"
CP_URL = "http://127.0.0.1:14000/api/"


REQUEST_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "channel_terms": {"type": "object"},  # TODO validate terms format
        "pubkey": {"type": "string"},
        "spend_secret_hash": {"type": "string"},
        "handle": {"type": "string"},
    },
    "required": ["channel_terms", "pubkey", "spend_secret_hash", "handle"],
    "additionalProperties": False
}


class TestMpcHubRequest(unittest.TestCase):

    def setUp(self):
        self.root = os.path.join(
            tempfile.mkdtemp(prefix="picopayments_test_"), "subdir"
        )
        self.server = Process(target=main, args=([
            "--testnet",
            "--root={0}".format(self.root),
            "--host={0}".format(HOST),
            "--port={0}".format(PORT),
            "--cp_url={0}".format(CP_URL)
        ],))
        self.server.start()
        time.sleep(5)  # wait until server started

    def tearDown(self):
        self.server.terminate()
        self.server.join()
        shutil.rmtree(self.root)

    def test_standard_usage_xcp(self):
        asset = "XCP"
        client_key = control.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        result = rpc.call(
            url=URL,
            method="mpc_hub_request",
            params={
                "asset": asset,
                "wif": client_key["wif"],
                "spend_secret_hash": secret_hash,
            },
            verify=False,
            jsonauth=True
        )
        self.assertIsNotNone(result)
        jsonschema.validate(result, REQUEST_RESULT_SCHEMA)

    def test_validate_asset_in_terms(self):

        def func():
            asset = "BADASSET"
            client_key = control.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            rpc.call(
                url=URL,
                method="mpc_hub_request",
                params={
                    "asset": asset,
                    "wif": client_key["wif"],
                    "spend_secret_hash": secret_hash,
                },
                verify=False,
                jsonauth=True
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(exceptions.AssetNotInTerms, func)

    def test_validate_url(self):

        def func():
            asset = "XCP"
            client_key = control.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            rpc.call(
                url=URL,
                method="mpc_hub_request",
                params={
                    "asset": asset,
                    "wif": client_key["wif"],
                    "spend_secret_hash": secret_hash,
                    "hub_rpc_url": "?? invalid url ??",
                },
                verify=False,
                jsonauth=True
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(exceptions.InvalidUrl, func)


if __name__ == "__main__":
    unittest.main()
