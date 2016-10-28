import os
import json
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments import etc
from micropayment_core import keys
from picopayments_client.mpc import Mpc
from tests.mock import MockAPI


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestUsrClientBlockSend(unittest.TestCase):

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

    def test_standard_usage(self):
        client = Mpc(MockAPI(verify_ssl_cert=False))
        src_wif = self.data["funded"]["gamma"]["wif"]
        asset = self.data["funded"]["gamma"]["asset"]
        wif = keys.generate_wif(netcode=etc.netcode)
        dest_address = keys.address_from_wif(wif)
        quantity = 42
        txid = client.block_send(
            source=src_wif, destination=dest_address, asset=asset,
            quantity=quantity, dryrun=True
        )
        self.assertIsNotNone(txid)


if __name__ == "__main__":
    unittest.main()
