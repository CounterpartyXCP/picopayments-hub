import os
import json
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments import auth
from picopayments import ctrl
from picopayments import cli
from picopayments import err
from picopayments import rpc
from picopayments import Client
from counterpartylib.lib.micropayments import util


rpc.CALL_LOCAL_PROCESS = True
CP_URL = "http://139.59.214.74:14000/api/"


class TestMpcHubSync(unittest.TestCase):

    # FIXME test fails if request made, deposit not made then sync

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        ctrl.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ]))
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_validate_handles_exist(self):

        def func():
            secret = ctrl.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [{
                    "payee_handle": "deadbeef",
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                "commit": None,
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mpc_hub_sync(**params)

        self.assertRaises(err.HandlesNotFound, func)

    def test_validate_revoke_format(self):

        def func():
            secret = ctrl.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [],
                "commit": None,
                "revokes": "invalidformat",
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mpc_hub_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_validate_commit_format(self):

        def func():
            secret = ctrl.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [],
                "commit": "invalidformat",
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mpc_hub_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_standard_commit(self):

        quantity = 5
        client = Client.deserialize(self.data["connections"]["alpha"])
        sync_fee = client.channel_terms["sync_fee"]
        commit = client.create_commit(quantity + sync_fee)
        h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
        h2c_next_revoke_secret_hash = util.hash160hex(
            h2c_next_revoke_secret_value
        )
        params = {
            "handle": client.handle,
            "sends": [{
                "payee_handle": client.handle,
                "amount": quantity,
                "token": "deadbeef"
            }],
            "commit": commit,
            "revokes": None,
            "next_revoke_secret_hash": h2c_next_revoke_secret_hash
        }
        params = auth.sign_json(params, client.client_wif)
        result = api.mpc_hub_sync(**params)

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
