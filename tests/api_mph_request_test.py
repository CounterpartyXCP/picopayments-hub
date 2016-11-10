import os
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments_client import auth
from picopayments import lib
from picopayments import srv
from picopayments import err
from micropayment_core import util
from micropayment_core import keys


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://127.0.0.1:14000/api/")


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
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ], serve=False)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @unittest.skip("FIXME setup mock counterpartylib")
    def test_standard_usage_xcp(self):
        asset = "XCP"
        client_key = lib.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {"asset": asset, "spend_secret_hash": secret_hash}
        privkey = keys.wif_to_privkey(client_key["wif"])
        params = auth.sign_json(params, privkey)
        result = api.mph_request(**params)

        self.assertIsNotNone(result)
        jsonschema.validate(result, REQUEST_RESULT_SCHEMA)

    @unittest.skip("FIXME setup mock counterpartylib")
    def test_validate_asset_in_terms(self):

        def func():
            asset = "TESTASSETONE"
            client_key = lib.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            params = {"asset": asset, "spend_secret_hash": secret_hash}
            privkey = keys.wif_to_privkey(client_key["wif"])
            params = auth.sign_json(params, privkey)
            api.mph_request(**params)

        self.assertRaises(err.AssetNotInTerms, func)

    @unittest.skip("FIXME setup mock counterpartylib")
    def test_validate_asset_exists(self):

        def func():
            asset = "NONEXISTINGASSET"
            client_key = lib.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            params = {"asset": asset, "spend_secret_hash": secret_hash}
            privkey = keys.wif_to_privkey(client_key["wif"])
            params = auth.sign_json(params, privkey)
            api.mph_request(**params)

        self.assertRaises(err.AssetDoesNotExist, func)

    @unittest.skip("FIXME setup mock counterpartylib")
    def test_validate_url(self):

        def func():
            asset = "XCP"
            client_key = lib.create_key(asset)
            secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            params = {
                "asset": asset,
                "spend_secret_hash": secret_hash,
                "hub_rpc_url": "?? invalid url ??",
            }
            privkey = keys.wif_to_privkey(client_key["wif"])
            params = auth.sign_json(params, privkey)
            api.mph_request(**params)

        self.assertRaises(err.InvalidUrl, func)


if __name__ == "__main__":
    unittest.main()
