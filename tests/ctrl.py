import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from picopayments import ctrl
from picopayments import cli
from picopayments import rpc
from picopayments import err


CP_URL = "http://127.0.0.1:14000/api/"
# CP_URL = "http://139.59.214.74:14000/api/"


@unittest.skip("FIXME")
class TestCtrl(unittest.TestCase):

    def setUp(self):
        self.basedir = tempfile.mkdtemp(prefix="picopayments_test_")
        ctrl.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ]))

    def tearDown(self):
        shutil.rmtree(self.basedir)

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

        def func():
            ctrl.read_current_terms("deadbeef")
        self.assertRaises(err.AssetNotInTerms, func)


if __name__ == "__main__":
    unittest.main()
