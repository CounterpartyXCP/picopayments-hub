import os
import shutil
import unittest
import tempfile
from counterpartylib.lib.micropayments import util
from picopayments import ctrl
from picopayments import api


class TestMpcHubRequest(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        ctrl.initialize(["--testnet", "--root={0}".format(self.root)])

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_standard_usage_xcp(self):
        asset = "XCP"
        client_key = ctrl.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        result = api.mpc_hub_request(asset, client_key["pubkey"],
                                     secret_hash, None)
        self.assertIsNotNone(result)

        # TODO test hub pubkey in db
        # TODO test recv spend secret in db
        # TODO test send micropayment channel created in db
        # TODO test recv micropayment channel created in db
        # TODO test hub connection created in db

    # TODO test raises exception on no terms for asset
    # TODO test input validation
