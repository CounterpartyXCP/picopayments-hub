import os
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments import auth
from picopayments import ctrl
from picopayments import cli
from picopayments import err
from counterpartylib.lib.micropayments import util


CP_URL = "http://139.59.214.74:14000/api/"


REQUEST_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "channel_terms": {"type": "object"},  # TODO validate terms format
        "pubkey": {"type": "string"},
        "signature": {"type": "string"},
        "spend_secret_hash": {"type": "string"},
        "handle": {"type": "string"},
    },
    "required": [
        "signature", "channel_terms", "pubkey", "spend_secret_hash", "handle"
    ],
    "additionalProperties": False
}


class TestMpcHubRequest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", basedir)
        ctrl.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(basedir),
            "--cp_url={0}".format(CP_URL)
        ]))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_standard_usage_xcp(self):
        asset = "XCP"
        client_key = ctrl.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {"asset": asset, "spend_secret_hash": secret_hash}
        params = auth.sign_json(params, client_key["wif"])
        result = api.mpc_hub_request(**params)

        self.assertIsNotNone(result)
        jsonschema.validate(result, REQUEST_RESULT_SCHEMA)

    def test_validate_asset_in_terms(self):

        def func():
            asset = "BADASSET"
            client_key = ctrl.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            params = {"asset": asset, "spend_secret_hash": secret_hash}
            params = auth.sign_json(params, client_key["wif"])
            api.mpc_hub_request(**params)

        self.assertRaises(err.AssetNotInTerms, func)

    def test_validate_url(self):

        def func():
            asset = "XCP"
            client_key = ctrl.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            params = {
                "asset": asset,
                "spend_secret_hash": secret_hash,
                "hub_rpc_url": "?? invalid url ??",
            }
            params = auth.sign_json(params, client_key["wif"])
            api.mpc_hub_request(**params)

        self.assertRaises(err.InvalidUrl, func)


if __name__ == "__main__":
    unittest.main()
