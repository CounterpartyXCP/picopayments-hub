import os
import json
import shutil
import unittest
import tempfile
from picopayments import api
from picopayments import sys
from picopayments import cli


CP_URL = "http://139.59.214.74:14000/api/"


class TestMpcHubTerms(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        sys.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ]))
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_standard_usage_xcp(self):
        # TODO test input validation

        # test gets all
        terms = api.mpc_hub_terms()
        self.assertEqual(terms, {
            "BTC": {
                "deposit_ratio": 1.0,
                "timeout_limit": 0,
                "sync_fee": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            },
            "XCP": {
                "deposit_ratio": 1.0,
                "timeout_limit": 0,
                "sync_fee": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            },
            "A14456548018133352000": {
                "deposit_ratio": 1.0,
                "timeout_limit": 0,
                "sync_fee": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            }
        })

        # test limits to asset
        terms = api.mpc_hub_terms(assets=["XCP"])
        self.assertEqual(terms, {
            "XCP": {
                "deposit_ratio": 1.0,
                "timeout_limit": 0,
                "sync_fee": 1,
                "setup_ttl": 2,
                "deposit_limit": 0
            }
        })


if __name__ == "__main__":
    unittest.main()
