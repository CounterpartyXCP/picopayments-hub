import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
# API_URL = "http://127.0.0.1:14000/api/"
API_URL = "http://45.55.201.116:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/deposit.fixtures.json"))


class TestDeposit(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def test_deposit(self):
        result = self.api.call(
            method="mpc_make_deposit",
            params={
                "asset": ASSET,
                "payer_pubkey": FIXTURES["payer_pubkey"],
                "payee_pubkey": FIXTURES["payee_pubkey"],
                "spend_secret_hash": FIXTURES["spend_secret_hash"],
                "expire_time": FIXTURES["expire_time"],
                "quantity": FIXTURES["quantity"]
            }
        )
        self.assertEqual(FIXTURES["expected_deposit_result"], result)

    def test_set_deposit(self):
        deposit_script = FIXTURES["expected_deposit_result"]["deposit_script"]
        expected_payee_pubkey = FIXTURES["payee_pubkey"]
        expected_spend_secret_hash = FIXTURES["spend_secret_hash"]
        result = self.api.call(
            method="mpc_set_deposit",
            params={
                "asset": ASSET,
                "deposit_script": deposit_script,
                "expected_payee_pubkey": expected_payee_pubkey,
                "expected_spend_secret_hash": expected_spend_secret_hash
            }
        )
        self.assertEqual(FIXTURES["expected_set_deposit_result"], result)


if __name__ == "__main__":
    unittest.main()
