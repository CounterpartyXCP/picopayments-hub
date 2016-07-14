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
        address = ctrl.get_funding_address("XCP")
        self.assertTrue(is_address_valid(address, allowable_netcodes=["XTN"]))

    def test_get_current_terms_id(self):
        # TODO test raises exception on no terms for asset

        # insert new terms and return id
        terms_id = ctrl.get_current_terms_id("XCP")
        self.assertEqual(terms_id, 1)

        # gets existing terms
        terms_id = ctrl.get_current_terms_id("XCP")
        self.assertEqual(terms_id, 1)


if __name__ == "__main__":
    unittest.main()
