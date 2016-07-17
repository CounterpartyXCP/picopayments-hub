import os
import shutil
import unittest
import tempfile
from pycoin.key.validate import is_address_valid
from counterpartylib.lib.micropayments import util
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

    def test_create_hub_connection(self):
        # TODO test raises exception on no terms for asset

        asset = "XCP"
        key = ctrl.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        result = ctrl.create_hub_connection(asset, key["pubkey"],
                                            secret_hash, None)
        self.assertIsNotNone(result)

        # TODO test hub pubkey in db
        # TODO test recv spend secret in db
        # TODO test send micropayment channel created in db
        # TODO test recv micropayment channel created in db
        # TODO test hub connection created in db


if __name__ == "__main__":
    unittest.main()
