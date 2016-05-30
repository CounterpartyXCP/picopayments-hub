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


class TestRecover(unittest.TestCase):

    def setUp(self):
        self.payer = picopayments.Channel(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def test_expired_to_recovering(self):
        self.payer.load(FIXTURES["test_expire"]["expired"])
        self.payer.payer_update()  # publish expire tx
        self.assertEqual(
            self.payer.save(), FIXTURES["test_expire"]["recovering_alpha"]
        )

    def test_recovering_to_closed(self):
        self.payer.load(FIXTURES["test_expire"]["recovering_beta"])
        self.payer.payer_update()  # does nothing
        self.assertEqual(
            self.payer.save(), FIXTURES["test_expire"]["recovering_beta"]
        )


if __name__ == "__main__":
    unittest.main()
