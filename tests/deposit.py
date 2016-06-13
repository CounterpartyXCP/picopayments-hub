import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/deposit.fixtures.json"))


class TestDeposit(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def test_deposit(self):
        result = self.api.payer_make_deposit(
            ASSET,
            FIXTURES["payer_pubkey"],
            FIXTURES["payee_pubkey"],
            FIXTURES["spend_secret_hash"],
            FIXTURES["expire_time"],
            FIXTURES["quantity"]
        )
        self.assertEqual(FIXTURES["expected_deposit_result"], result)

    def test_set_deposit(self):
        deposit_script = FIXTURES["expected_deposit_result"]["deposit_script"]
        expected_payee_pubkey = FIXTURES["payee_pubkey"]
        expected_spend_secret_hash = FIXTURES["spend_secret_hash"]
        result = self.api.payee_set_deposit(
            ASSET, deposit_script, expected_payee_pubkey,
            expected_spend_secret_hash
        )
        self.assertEqual(FIXTURES["expected_set_deposit_result"], result)


if __name__ == "__main__":
    unittest.main()
