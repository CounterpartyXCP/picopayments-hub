import os
import json
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments_client import mph
from tests.mock import MockAPI


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://127.0.0.1:14000/api/")


class TestUsrClientConnect(unittest.TestCase):

    # FIXME test fails if request made, deposit not made then sync

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
        verify_ssl_cert = False
        auth_wif = self.data["funded"]["alpha"]["wif"]
        asset = self.data["funded"]["alpha"]["asset"]
        rpc_api = MockAPI(url="http://127.0.0.1:15000/api/", auth_wif=auth_wif,
                          verify_ssl_cert=verify_ssl_cert)
        client = mph.Mph(rpc_api)
        txid = client.connect(1337, 65535, asset=asset, dryrun=True)
        self.assertIsNotNone(txid)


if __name__ == "__main__":
    unittest.main()
