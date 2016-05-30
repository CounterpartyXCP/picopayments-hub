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
        payer_state = FIXTURES["test_expire"]["expired"]
        result = self.payer.payer_update(payer_state)  # publish expire tx
        payer_state = result["channel_state"]
        self.assertEqual(
            payer_state, FIXTURES["test_expire"]["recovering_alpha"]
        )

    def test_recovering_to_closed(self):
        payer_state = FIXTURES["test_expire"]["recovering_beta"]
        result = self.payer.payer_update(payer_state)  # does nothing
        payer_state = result["channel_state"]
        self.assertEqual(
            payer_state, FIXTURES["test_expire"]["recovering_beta"]
        )


if __name__ == "__main__":
    unittest.main()
