import shutil
import time
import unittest
import tempfile
from picopayments.main import main
from multiprocessing import Process
from picopayments.control import rpc_call


HOST = "127.0.0.1"
PORT = "15000"
URL = "https://127.0.0.1:15000/api/"
CP_URL = "http://127.0.0.1:14000/api/"


class TestMpcHubTerms(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        self.server = Process(target=main, args=([
            "--testnet",
            "--root={0}".format(self.root),
            "--host={0}".format(HOST),
            "--port={0}".format(PORT),
            "--cp_url={0}".format(CP_URL)
        ],))
        self.server.start()
        time.sleep(5)  # wait until server started

    def tearDown(self):
        self.server.terminate()
        self.server.join()
        shutil.rmtree(self.root)

    def test_standard_usage_xcp(self):
        # TODO test input validation

        # test gets all
        terms = rpc_call(
            url=URL,
            method="mpc_hub_terms",
            params={},
            verify=False
        )
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
        terms = rpc_call(
            url=URL,
            method="mpc_hub_terms",
            params={
                "assets": ["XCP"]
            },
            verify=False
        )
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


if __name__ == "__main__":
    unittest.main()
