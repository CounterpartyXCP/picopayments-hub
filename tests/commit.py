import os
import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/commit.fixtures.json"))

PAYER_BEFORE = FIXTURES["payer_before"]
PAYEE_BEFORE_CLOSE = FIXTURES["payee_before_close"]
PAYEE_BEFORE_REQUEST = FIXTURES["payee_before_request"]
REVOKE_SECRET_HASH = FIXTURES["revoke_secret_hash"]
PAYEE_AFTER_REQUEST = FIXTURES["payee_after_request"]
SET_COMMIT_RESULT = FIXTURES["set_commit_result"]
SET_COMMIT = FIXTURES["set_commit"]
DELAY_TIME = FIXTURES["delay_time"]
PAYEE_CLOSED = FIXTURES["payee_closed"]


class TestCommit(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.maxDiff = None

    def test_create_commit(self):
        result = self.api.payer_create_commit(
            PAYER_BEFORE, 1, REVOKE_SECRET_HASH, DELAY_TIME
        )
        self.assertEqual(result, FIXTURES["create_commit_result"])

    def test_set_commit(self):
        result = self.api.payee_add_commit(
            PAYEE_AFTER_REQUEST,
            SET_COMMIT["rawtx"],
            SET_COMMIT["script"]
        )
        self.assertEqual(result, SET_COMMIT_RESULT)

    def test_funds_flow(self):
        payer_state = PAYER_BEFORE
        payee_state = PAYEE_BEFORE_REQUEST

        secrets = {}  # hash -> secret

        # send funds
        for quantity in range(1, 10):

            secret = picopayments.util.b2h(os.urandom(32))
            secret_hash = picopayments.util.hash160hex(secret)
            secrets[secret_hash] = secret

            result = self.api.payee_request_commit(
                payee_state, quantity, secret_hash
            )
            payee_state = result["state"]

            result = self.api.payer_create_commit(
                payer_state, result["quantity"],
                result["revoke_secret_hash"],
                DELAY_TIME
            )
            payer_state = result["state"]
            rawtx = result["tosign"]["rawtx"]
            # FIXME sign here
            commit_script = result["commit_script"]

            result = self.api.payee_add_commit(payee_state, rawtx,
                                               commit_script)
            payee_state = result["state"]

        self.assertEqual(self.api.get_transferred_amount(payer_state), 9)
        self.assertEqual(self.api.get_transferred_amount(payee_state), 9)

        # payee reviels secrets
        secret_hashes = self.api.payee_revoke_secret_hashes_above(
            payee_state, 4
        )
        revoke_secrets = [secrets[sh] for sh in secret_hashes]

        # payee revokes commits
        result = self.api.revoke_all(payee_state, revoke_secrets)
        payee_state = result["state"]
        self.assertEqual(self.api.get_transferred_amount(payee_state), 4)

        # payer revokes commits
        result = self.api.revoke_all(payer_state, revoke_secrets)
        payer_state = result["state"]
        self.assertEqual(self.api.get_transferred_amount(payer_state), 4)

    def test_close(self):
        result = self.api.payee_highest_commit(PAYEE_BEFORE_CLOSE)
        self.assertEqual(result, FIXTURES["expected_close_result"])


if __name__ == "__main__":
    unittest.main()
