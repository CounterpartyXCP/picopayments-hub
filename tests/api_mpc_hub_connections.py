import os
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments import auth
from picopayments import ctrl
from picopayments import cli


CP_URL = "http://139.59.214.74:14000/api/"


CONNECTION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "handle": {"type": "string"},
        "client2hub_deposit_script": {"type": "string"},
        "hub2client_deposit_script": {"type": "string"},
        "pubkey": {"type": "string"},
        "signature": {"type": "string"},
        "client_url": {"type": ["string", "null"]},
    },
    "required": [
        "asset", "handle", "client_url",
        "client2hub_deposit_script", "hub2client_deposit_script",
        "pubkey", "signature"
    ],
    "additionalProperties": False
}


class TestMpcHubConnections(unittest.TestCase):

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

    def test_all(self):
        connections = api.mpc_hub_connections()
        # self.assertTrue(len(connections) > 0)
        for connection in connections:
            jsonschema.validate(connection, CONNECTION_RESULT_SCHEMA)
            auth.verify_json(connection)
            # FIXME validate pubkey matches hub deposit script payer

    def test_filters_assets(self):
        pass

    def test_filters_handles(self):
        pass

    def test_verifies_assets(self):
        pass

    def test_verifies_handles(self):
        pass
