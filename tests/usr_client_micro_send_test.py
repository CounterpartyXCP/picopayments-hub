import os
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments_client.mph import Mph
from tests.util import MockAPI


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://127.0.0.1:14000/api/")


class TestUsrClientMicroSend(unittest.TestCase):

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
    def test_predefined_token(self):
        connection = self.data["connections"]["alpha"]
        client = Mph.deserialize(data=connection, api_cls=MockAPI)
        self.assertEqual(client.payments_queued, [])
        token = client.micro_send("f483", 42, "deadbeef")
        self.assertEqual(token, "deadbeef")
        self.assertEqual(client.payments_queued, [{
            "payee_handle": "f483",
            "amount": 42,
            "token": "deadbeef"
        }])

    @unittest.skip("FIXME")
    def test_generated_token(self):
        connection = self.data["connections"]["alpha"]
        client = Mph.deserialize(data=connection, api_cls=MockAPI)
        self.assertEqual(client.payments_queued, [])
        token = client.micro_send("f483", 42)
        self.assertEqual(client.payments_queued, [{
            "payee_handle": "f483",
            "amount": 42,
            "token": token
        }])


if __name__ == "__main__":
    unittest.main()
