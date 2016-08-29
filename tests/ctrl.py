import os
import json
import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from picopayments import ctrl
from picopayments import cli
from picopayments import rpc
from picopayments import err


CP_URL = "http://127.0.0.1:14000/api/"


class TestCtrl(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        ctrl.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ]))
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_get_funding_addresses(self):
        assets = ["XCP"]
        result = ctrl.create_funding_addresses(assets)
        assert(assets == list(result.keys()))
        self.assertTrue(all([
            is_address_valid(a, allowable_netcodes=["XTN"])
            for a in result.values()
        ]))

    def test_failed_rpc_call(self):

        def func():
            rpc.cp_call(method="nonexistant", params={})
        self.assertRaises(err.RpcCallFailed, func)

    def test_validate_read_unknown_asset(self):

        terms = ctrl.terms(["deadbeef"])
        self.assertEqual(terms, {})


if __name__ == "__main__":
    unittest.main()
