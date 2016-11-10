import os
import json
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments_client.mph import Mph
from tests.util import MockAPI


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://127.0.0.1:14000/api/")


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

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @unittest.skip("FIXME")
    def test_standard_usage(self):
        connection = self.data["connections"]["alpha"]
        client = Mph.deserialize(data=connection, api_cls=MockAPI)
        self.assertEqual(connection, client.serialize())


if __name__ == "__main__":
    unittest.main()
