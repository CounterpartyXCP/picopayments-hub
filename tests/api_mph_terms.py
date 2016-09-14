import os
import json
import shutil
import unittest
import tempfile
from picopayments import api
from picopayments import srv


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestMpcHubTerms(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ], serve=False)
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_standard_usage_xcp(self):
        # TODO test input validation

        # test gets all
        terms = api.mph_terms()
        self.assertEqual(terms, {
            "BTC": {
                "deposit_max": 0,
                "deposit_min": 0,
                "deposit_ratio": 1.0,
                "expire_max": 0,
                "expire_min": 0,
                "sync_fee": 1
            },
            "XCP": {
                "deposit_max": 0,
                "deposit_min": 0,
                "deposit_ratio": 1.0,
                "expire_max": 0,
                "expire_min": 0,
                "sync_fee": 1
            },
            "A14456548018133352000": {
                "deposit_max": 0,
                "deposit_min": 0,
                "deposit_ratio": 1.0,
                "expire_max": 0,
                "expire_min": 0,
                "sync_fee": 1
            }
        })

        # test limits to asset
        terms = api.mph_terms(assets=["XCP"])
        self.assertEqual(terms, {
            "XCP": {
                "deposit_max": 0,
                "deposit_min": 0,
                "deposit_ratio": 1.0,
                "expire_max": 0,
                "expire_min": 0,
                "sync_fee": 1
            },
        })


if __name__ == "__main__":
    unittest.main()
