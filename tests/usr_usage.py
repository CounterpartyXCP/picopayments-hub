import os
import json
import shutil
import unittest
import tempfile
from picopayments import etc
from picopayments import srv
from picopayments import Client


etc.call_local_process = True
CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestUsr(unittest.TestCase):

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

        clients = {}
        for name in ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]:
            client = Client.deserialize(self.data["connections"]["alpha"])
            self.assertTrue(client.is_connected())
            self.assertFalse(client.is_expired())
            print(
                name,
                "=",
                json.dumps(client.get_status(), indent=2, sort_keys=True)
            )

            clients[name] = client


if __name__ == "__main__":
    unittest.main()
