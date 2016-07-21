import os
import shutil
import unittest
import tempfile
from pycoin.serialize import b2h
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import compile_deposit_script
from picopayments import ctrl
from picopayments import api


class TestMpcHubDeposit(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        ctrl.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_mpc_hub_deposit(self):

        asset = "XCP"
        client_key = ctrl.create_key(asset)
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

        # TODO test send channel updated
        # TODO test receive channel updated
        # TODO test secret saved


if __name__ == "__main__":
    unittest.main()
