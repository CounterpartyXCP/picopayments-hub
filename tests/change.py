import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
# API_URL = "http://127.0.0.1:14000/api/"
API_URL = "http://45.55.201.116:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/change.fixtures.json"))


class TestRecoverChange(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def test_recover_change(self):
        result = self.api.call(
            "mpc_recoverables",
            {
                "state": FIXTURES["payer_state"]
            }
        )
        self.assertEqual(result, FIXTURES["expected_result"])


if __name__ == "__main__":
    unittest.main()
