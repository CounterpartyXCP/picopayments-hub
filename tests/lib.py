import os
import json
import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from picopayments import lib
from picopayments import srv


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestLIB(unittest.TestCase):

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

    def test_get_funding_addresses(self):
        assets = ["XCP"]
        result = lib.get_funding_addresses(assets)
        assert(assets == list(result.keys()))
        self.assertTrue(all([
            is_address_valid(a, allowable_netcodes=["XTN"])
            for a in result.values()
        ]))

    def test_validate_read_unknown_asset(self):

        terms = lib.terms(["deadbeef"])
        self.assertEqual(terms, {})


if __name__ == "__main__":
    unittest.main()
