import os
import json
import unittest
import shutil
import tempfile
from pycoin.serialize import b2h
from picopayments import srv
from picopayments import db


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestDB(unittest.TestCase):

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

    def test_handle_exists(self):

        def _create_connection(handle):
            db.add_hub_connection({
                "asset": b2h(os.urandom(32)),

                "deposit_max": 0,
                "deposit_min": 0,
                "deposit_ratio": 1.0,
                "expire_max": 0,
                "expire_min": 0,
                "sync_fee": 1,

                "hub_wif": b2h(os.urandom(32)),
                "hub_pubkey": b2h(os.urandom(32)),
                "hub_address": b2h(os.urandom(32)),
                "client_pubkey": b2h(os.urandom(32)),
                "client_address": b2h(os.urandom(32)),
                "secret_hash": b2h(os.urandom(32)),
                "secret_value": b2h(os.urandom(32)),
                "h2c_spend_secret_hash": b2h(os.urandom(32)),
                "handle": handle,
                "hub_rpc_url": b2h(os.urandom(32)),
            })

        _create_connection("a")
        _create_connection("b")

        self.assertTrue(db.handles_exist(["a"]))  # test single
        self.assertTrue(db.handles_exist(["b"]))  # test single
        self.assertTrue(db.handles_exist(["a", "b"]))  # test multiple
        self.assertFalse(db.handles_exist(["c"]))  # test missing single
        self.assertFalse(db.handles_exist(["a", "c"]))  # test one missing
        self.assertFalse(db.handles_exist(["c", "d"]))  # test all missing


if __name__ == "__main__":
    unittest.main()
