import shutil
import unittest
import tempfile
from picopayments import control
from picopayments import api


class TestMpcHubTerms(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        control.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_standard_usage_xcp(self):
        # TODO test input validation

        # test gets all
        terms = api.mpc_hub_terms()
        self.assertEqual(terms, {
            "BTC": {
                "deposit_ratio": 1.0,
                "fee_setup": 10,
                "timeout_limit": 0,
                "fee_sync": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            },
            "XCP": {
                "deposit_ratio": 1.0,
                "fee_setup": 10,
                "timeout_limit": 0,
                "fee_sync": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            },
            "A14456548018133352000": {
                "deposit_ratio": 1.0,
                "fee_setup": 10,
                "timeout_limit": 0,
                "fee_sync": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            }
        })

        # test limits to asset
        terms = api.mpc_hub_terms("XCP")
        self.assertEqual(terms, {
            "XCP": {
                "deposit_ratio": 1.0,
                "fee_setup": 10,
                "timeout_limit": 0,
                "fee_sync": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            }
        })
