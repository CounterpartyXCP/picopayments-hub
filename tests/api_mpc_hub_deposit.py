import os
import shutil
import unittest
import tempfile
from pycoin.serialize import b2h
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import compile_deposit_script
from picopayments import control
from picopayments import api
from picopayments import exceptions
import jsonschema


DEPOSIT_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "deposit_script": {"type": "string"},
        "next_revoke_secret_hash": {"type": "string"},
    },
    "required": ["deposit_script", "next_revoke_secret_hash"],
    "additionalProperties": False
}


class TestMpcHubDeposit(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        control.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_standard_usage_xcp(self):

        asset = "XCP"
        client_key = control.create_key(asset)
        client_pubkey = client_key["pubkey"]

        hub2client_spend_secret = util.b2h(os.urandom(32))
        hub2client_spend_secret_hash = util.hash160hex(hub2client_spend_secret)

        result = api.mpc_hub_request(asset, client_pubkey,
                                     hub2client_spend_secret_hash, None)
        handle = result["handle"]
        hub_pubkey = result["pubkey"]
        client2hub_spend_secret_hash = result["spend_secret_hash"]

        client2hub_deposit_script = b2h(compile_deposit_script(
            client_pubkey, hub_pubkey, client2hub_spend_secret_hash, 1337
        ))

        result = api.mpc_hub_deposit(
            handle, client2hub_deposit_script,
            util.hash160hex(util.b2h(os.urandom(32)))
        )
        self.assertIsNotNone(result)
        jsonschema.validate(result, DEPOSIT_RESULT_SCHEMA)

    def test_validate_deposit_not_already_given(self):

        def func():

            asset = "XCP"
            client_key = control.create_key(asset)
            client_pubkey = client_key["pubkey"]

            hub2client_spend_secret = util.b2h(os.urandom(32))
            hub2client_spend_secret_hash = util.hash160hex(
                hub2client_spend_secret
            )

            result = api.mpc_hub_request(asset, client_pubkey,
                                         hub2client_spend_secret_hash, None)
            handle = result["handle"]
            hub_pubkey = result["pubkey"]
            client2hub_spend_secret_hash = result["spend_secret_hash"]

            client2hub_deposit_script = b2h(compile_deposit_script(
                client_pubkey, hub_pubkey, client2hub_spend_secret_hash, 1337
            ))

            # submit deposit
            result = api.mpc_hub_deposit(
                handle, client2hub_deposit_script,
                util.hash160hex(util.b2h(os.urandom(32)))
            )
            self.assertIsNotNone(result)

            # resubmit deposit
            api.mpc_hub_deposit(
                handle, client2hub_deposit_script,
                util.hash160hex(util.b2h(os.urandom(32)))
            )

        self.assertRaises(exceptions.DepositAlreadyGiven, func)

    def test_validate_handle_exists(self):

        def func():

            result = api.mpc_hub_deposit(
                "deadbeef",
                util.b2h(os.urandom(32)),
                util.hash160hex(util.b2h(os.urandom(32)))
            )
            self.assertIsNotNone(result)

        self.assertRaises(exceptions.HandleNotFound, func)


if __name__ == "__main__":
    unittest.main()
