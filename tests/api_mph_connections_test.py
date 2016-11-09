import os
import json
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments_client import auth
from picopayments import srv


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://127.0.0.1:14000/api/")


CONNECTION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "handle": {"type": "string"},
        "c2h_deposit_script": {"type": "string"},
        "h2c_deposit_script": {"type": "string"},
        "pubkey": {"type": "string"},
        "signature": {"type": "string"},
        "client_url": {"type": ["string", "null"]},
    },
    "required": [
        "asset", "handle", "client_url",
        "c2h_deposit_script", "h2c_deposit_script",
        "pubkey", "signature"
    ],
    "additionalProperties": False
}


class TestMpcHubConnections(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ], serve=False)
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_all(self):
        connections = api.mph_connections()
        self.assertTrue(len(connections) == 7)
        for connection in connections:
            jsonschema.validate(connection, CONNECTION_RESULT_SCHEMA)
            auth.verify_json(connection)
            # FIXME validate pubkey matches hub deposit script payer

    @unittest.skip("FIXME setup mock counterpartylib")
    def test_filters_assets(self):

        connection = self.data["connections"]["alpha"]
        asset = connection["c2h_state"]["asset"]
        connections = api.mph_connections(assets=[asset])
        self.assertTrue(len(connections) == 7)
        for connection in connections:
            self.assertEqual(connection["asset"], asset)

        connection = self.data["connections"]["alpha"]
        asset = connection["c2h_state"]["asset"]
        connections = api.mph_connections(assets=["XCP"])
        self.assertTrue(len(connections) == 0)

    def test_filters_handles(self):
        handles = [
            self.data["connections"]["alpha"]["handle"],
            self.data["connections"]["beta"]["handle"],
            self.data["connections"]["gamma"]["handle"]
        ]
        connections = api.mph_connections(handles=handles)
        self.assertTrue(len(connections) == 3)
        for connection in connections:
            self.assertIn(connection["handle"], handles)

    def test_verifies_assets(self):
        pass  # FIXME test it

    def test_verifies_handles(self):
        pass  # FIXME test it


if __name__ == "__main__":
    unittest.main()
