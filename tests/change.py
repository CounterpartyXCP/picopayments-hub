import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/fixtures.json"))
SPEND_SECRET = FIXTURES["test_change"]["payee_state"]["spend_secret"]


class TestRecoverChange(unittest.TestCase):

    def setUp(self):
        self.payer = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.payer.stop()

    def test_find_spend_secret(self):
        self.payer.load(FIXTURES["test_change"]["payer_state"])

        secret = self.payer.find_spend_secret()
        self.assertEqual(secret, SPEND_SECRET)


if __name__ == "__main__":
    unittest.main()
