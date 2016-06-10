import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/expire.fixtures.json"))


class TestRecover(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def test_expired_to_recovering(self):
        payer_state = FIXTURES["expired"]
        result = self.api.payer_update(payer_state)  # publish expire tx
        self.assertEqual(result, FIXTURES["recovering_alpha"])

    def test_recovering_to_closed(self):
        payer_state = FIXTURES["recovering_beta"]
        result = self.api.payer_update(payer_state)  # does nothing
        self.assertEqual(result, FIXTURES["recovering_beta_result"])


if __name__ == "__main__":
    unittest.main()
