import os
import json
import shutil
import unittest
import tempfile
from picopayments import etc
from picopayments import srv
from picopayments import HubClient


etc.call_local_process = True
CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestUsrClientSerialization(unittest.TestCase):

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
        connection = self.data["connections"]["alpha"]
        client = HubClient.deserialize(connection)
        self.assertEqual(connection, client.serialize())


if __name__ == "__main__":
    unittest.main()
