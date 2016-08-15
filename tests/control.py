import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from picopayments import control
from picopayments import cli
from picopayments import rpc
from picopayments import exceptions


CP_URL = "http://139.59.214.74:14000/api/"


class TestCtrl(unittest.TestCase):

    def setUp(self):
        self.basedir = tempfile.mkdtemp(prefix="picopayments_test_")
        control.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ]))

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_get_funding_addresses(self):
        assets = ["XCP"]
        result = control.create_funding_addresses(assets)
        assert(assets == list(result.keys()))
        self.assertTrue(all([
            is_address_valid(a, allowable_netcodes=["XTN"])
            for a in result.values()
        ]))

    def test_failed_rpc_call(self):

        def func():
            rpc.counterparty_call(method="nonexistant", params={})
        self.assertRaises(exceptions.RpcCallFailed, func)

    def test_validate_read_unknown_asset(self):

        def func():
            control.read_current_terms("deadbeef")
        self.assertRaises(exceptions.AssetNotInTerms, func)


if __name__ == "__main__":
    unittest.main()
