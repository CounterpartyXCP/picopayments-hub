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
from pycoin.serialize import b2h
from counterpartylib.lib.micropayments.scripts import compile_deposit_script


# CP_URL = "http://127.0.0.1:14000/api/"
CP_URL = "http://139.59.214.74:14000/api/"


DEPOSIT_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "deposit_script": {"type": "string"},
        "next_revoke_secret_hash": {"type": "string"},
        "signature": {"type": "string"},
        "pubkey": {"type": "string"},
    },
    "required": [
        "deposit_script", "next_revoke_secret_hash", "signature", "pubkey"
    ],
    "additionalProperties": False
}


@unittest.skip("FIXME")
class TestMpcHubDeposit(unittest.TestCase):

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
        client_key = ctrl.create_key(asset, netcode="XTN")
        client_pubkey = client_key["pubkey"]

        hub2client_spend_secret = util.b2h(os.urandom(32))
        hub2client_spend_secret_hash = util.hash160hex(hub2client_spend_secret)

        params = {
            "asset": asset,
            "spend_secret_hash": hub2client_spend_secret_hash
        }
        params = auth.sign_json(params, client_key["wif"])
        result = api.mpc_hub_request(**params)

        handle = result["handle"]
        hub_pubkey = result["pubkey"]
        client2hub_spend_secret_hash = result["spend_secret_hash"]

        client2hub_deposit_script = b2h(compile_deposit_script(
            client_pubkey, hub_pubkey, client2hub_spend_secret_hash, 1337
        ))

        next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {
            "handle": handle,
            "deposit_script": client2hub_deposit_script,
            "next_revoke_secret_hash": next_revoke_secret_hash
        }
        params = auth.sign_json(params, client_key["wif"])
        result = api.mpc_hub_deposit(**params)

        self.assertIsNotNone(result)
        jsonschema.validate(result, DEPOSIT_RESULT_SCHEMA)

    def test_validate_deposit_not_already_given(self):

        def func():

            asset = "XCP"
            client_key = ctrl.create_key(asset, netcode="XTN")
            client_pubkey = client_key["pubkey"]

            hub2client_spend_secret = util.b2h(os.urandom(32))
            hub2client_spend_secret_hash = util.hash160hex(
                hub2client_spend_secret
            )

            params = {
                "asset": asset,
                "spend_secret_hash": hub2client_spend_secret_hash
            }
            params = auth.sign_json(params, client_key["wif"])
            result = api.mpc_hub_request(**params)

            handle = result["handle"]
            hub_pubkey = result["pubkey"]
            client2hub_spend_secret_hash = result["spend_secret_hash"]

            client2hub_deposit_script = b2h(compile_deposit_script(
                client_pubkey, hub_pubkey, client2hub_spend_secret_hash, 1337
            ))

            # submit deposit
            next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))

            params = {
                "handle": handle,
                "deposit_script": client2hub_deposit_script,
                "next_revoke_secret_hash": next_revoke_secret_hash
            }
            params = auth.sign_json(params, client_key["wif"])
            result = api.mpc_hub_deposit(**params)
            self.assertIsNotNone(result)

            # resubmit deposit
            next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            params = {
                "handle": handle,
                "deposit_script": client2hub_deposit_script,
                "next_revoke_secret_hash": next_revoke_secret_hash
            }
            params = auth.sign_json(params, client_key["wif"])
            result = api.mpc_hub_deposit(**params)

        self.assertRaises(err.DepositAlreadyGiven, func)

    def test_validate_handle_exists(self):

        def func():

            asset = "XCP"
            client_key = ctrl.create_key(asset, netcode="XTN")
            next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            client2hub_deposit_script = util.b2h(os.urandom(32)),

            params = {
                "handle": "deadbeef",
                "deposit_script": client2hub_deposit_script,
                "next_revoke_secret_hash": next_revoke_secret_hash
            }
            params = auth.sign_json(params, client_key["wif"])
            api.mpc_hub_deposit(**params)

        self.assertRaises(err.HandleNotFound, func)


if __name__ == "__main__":
    unittest.main()
