import unittest
import shutil
import tempfile
from picopayments import ctrl
from picopayments import db


class TestDB(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        # TODO start mock counterparty service
        ctrl.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_new_connection_unique(self):
        db.add_hub_connection({
            "asset": "asset",

            # terms
            "setup_ttl": "setup_ttl",
            "deposit_limit": "deposit_limit",
            "deposit_ratio": "deposit_ratio",
            "timeout_limit": "timeout_limit",
            "fee_setup": "fee_setup",
            "fee_sync": "fee_sync",

            # hub key
            "hub_wif": "hub_wif",
            "hub_pubkey": "hub_pubkey",
            "hub_address": "hub_address",

            # client key
            "client_pubkey": "client_pubkey",
            "client_address": "client_address",

            # spend secret for receive channel
            "secret_hash": "secret_hash",
            "secret_value": "secret_value",

            # send micropayment channel
            "send_spend_secret_hash": "send_spend_secret_hash",

            # connection
            "handle": "handle",
            "hub_rpc_url": "hub_rpc_url",
        })
        # TODO check hub connection added
        # TODO check send channel added
        # TODO check recv channel added
        # TODO check key added
        # TODO check secret added
        # TODO check terms added


if __name__ == "__main__":
    unittest.main()
