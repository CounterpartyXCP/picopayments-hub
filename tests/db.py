import unittest
import shutil
import tempfile
from picopayments import ctrl
from picopayments import db


class TestDB(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_")
        # TODO start mock counterparty service
        ctrl.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_new_connection(self):
        # FIXME checks tyes and constranits
        db.new_connection({
            "asset": "asset",

            # Terms
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
            "send_deposit_script": "send_deposit_script",
            "send_cached_deposit_address": "send_cached_deposit_address",
            "hub_pubkey": "hub_pubkey",
            "hub_address": "hub_address",
            "send_cached_expire_time": "send_cached_expire_time",
            "send_cached_spend_secret_hash": "send_cached_spend_secret_hash",

            # send micropayment channel
            "recv_deposit_script": "recv_deposit_script",
            "recv_cached_deposit_address": "recv_cached_deposit_address",
            "hub_pubkey": "hub_pubkey",
            "hub_address": "hub_address",
            "recv_cached_expire_time": "recv_cached_expire_time",
            "secret_hash": "secret_hash",

            # connection
            "handle": "handle",
            "hub_rpc_url": "hub_rpc_url",
        })


if __name__ == "__main__":
    unittest.main()
