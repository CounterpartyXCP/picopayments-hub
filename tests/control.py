import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from picopayments import control
from picopayments import cli
from picopayments import rpc
from picopayments import exceptions


URL = "http://127.0.0.1:14000/api/"


class TestCtrl(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        # TODO start mock counterparty service
        control.initialize(cli.parse([
            "--testnet",
            "--root={0}".format(self.root),
            "--cp_url={0}".format(URL)
        ]))

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_get_funding_address(self):
        address = control.create_funding_address("XCP")
        self.assertTrue(is_address_valid(address, allowable_netcodes=["XTN"]))

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
