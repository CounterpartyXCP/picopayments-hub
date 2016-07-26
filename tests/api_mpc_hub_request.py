import os
import jsonschema
import shutil
import unittest
import tempfile
from counterpartylib.lib.micropayments import util
from picopayments import control
from picopayments import api
from picopayments import exceptions


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
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        control.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_standard_usage_xcp(self):
        asset = "XCP"
        client_key = control.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        result = api.mpc_hub_request(asset=asset, pubkey=client_key["pubkey"],
                                     spend_secret_hash=secret_hash,
                                     hub_rpc_url=None)
        self.assertIsNotNone(result)
        jsonschema.validate(result, REQUEST_RESULT_SCHEMA)

    def test_validate_asset_in_terms(self):

        def func():
            asset = "BADASSET"
            client_key = control.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            api.mpc_hub_request(asset=asset, pubkey=client_key["pubkey"],
                                spend_secret_hash=secret_hash,
                                hub_rpc_url=None)

        self.assertRaises(exceptions.AssetNotInTerms, func)

    def test_validate_url(self):

        def func():
            asset = "XCP"
            client_key = control.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            api.mpc_hub_request(asset=asset, pubkey=client_key["pubkey"],
                                spend_secret_hash=secret_hash,
                                hub_rpc_url="?? invalid url ??")

        self.assertRaises(exceptions.InvalidUrl, func)
