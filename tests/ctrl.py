import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from picopayments import ctrl


class TestCtrl(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        # TODO start mock counterparty service
        ctrl.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_get_funding_address(self):
        address = ctrl.create_funding_address("XCP")
        self.assertTrue(is_address_valid(address, allowable_netcodes=["XTN"]))


if __name__ == "__main__":
    unittest.main()
