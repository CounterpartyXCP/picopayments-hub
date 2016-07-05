import os
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


FIXTURES = json.load(open("tests/commit.fixtures.json"))


PAYER_BEFORE = FIXTURES["payer_before"]
PAYEE_BEFORE_CLOSE = FIXTURES["payee_before_close"]
PAYEE_BEFORE_REQUEST = FIXTURES["payee_before_request"]
REVOKE_SECRET_HASH = FIXTURES["revoke_secret_hash"]
PAYEE_AFTER_REQUEST = FIXTURES["payee_after_request"]
ADD_COMMIT_RESULT = FIXTURES["add_commit_result"]
SET_COMMIT = FIXTURES["set_commit"]
DELAY_TIME = FIXTURES["delay_time"]
PAYEE_CLOSED = FIXTURES["payee_closed"]


class TestCommit(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.maxDiff = None

    def test_create_commit(self):
        result = self.api.call(
            method="mpc_create_commit",
            params={
                "state": PAYER_BEFORE,
                "quantity": 1,
                "revoke_secret_hash": REVOKE_SECRET_HASH,
                "delay_time": DELAY_TIME,
            }
        )
        self.assertEqual(result, FIXTURES["create_commit_result"])

    def test_add_commit(self):
        payee_state = self.api.call(
            method="mpc_add_commit",
            params={
                "state": PAYEE_AFTER_REQUEST,
                "commit_rawtx": SET_COMMIT["rawtx"],
                "commit_script": SET_COMMIT["script"]
            }
        )
        self.assertEqual(payee_state, ADD_COMMIT_RESULT)

    def test_funds_flow(self):
        payer_state = PAYER_BEFORE
        payee_state = PAYEE_BEFORE_REQUEST

        secrets = {}  # hash -> secret

        # send funds
        for quantity in range(1, 10):

            secret = picopayments.util.b2h(os.urandom(32))
            secret_hash = picopayments.util.hash160hex(secret)
            secrets[secret_hash] = secret

            result = self.api.call(
                method="mpc_request_commit",
                params={
                    "state": payee_state,
                    "quantity": quantity,
                    "revoke_secret_hash": secret_hash,
                }
            )
            payee_state = result["state"]

            result = self.api.call(
                method="mpc_create_commit",
                params={
                    "state": payer_state,
                    "quantity": result["quantity"],
                    "revoke_secret_hash": result["revoke_secret_hash"],
                    "delay_time": DELAY_TIME,
                }
            )
            payer_state = result["state"]
            rawtx = result["tosign"]["commit_rawtx"]
            # FIXME sign here
            commit_script = result["commit_script"]

            payee_state = self.api.call(
                method="mpc_add_commit",
                params={
                    "state": payee_state,
                    "commit_rawtx": rawtx,
                    "commit_script": commit_script
                }
            )

        self.assertEqual(
            self.api.call(
                method="mpc_transferred_amount",
                params={"state": payer_state}
            ),
            9
        )
        self.assertEqual(
            self.api.call(
                method="mpc_transferred_amount",
                params={
                    "state": payee_state
                }
            ),
            9
        )

        # payee reviels secrets
        secret_hashes = self.api.call(
            method="mpc_revoke_secret_hashes_above",
            params={
                "state": payee_state,
                "quantity": 4
            }
        )
        revoke_secrets = [secrets[sh] for sh in secret_hashes]

        # payee revokes commits
        payee_state = self.api.call(
            method="mpc_revoke_all",
            params={
                "state": payee_state,
                "secrets": revoke_secrets
            }
        )
        self.assertEqual(
            self.api.call(
                method="mpc_transferred_amount",
                params={
                    "state": payee_state
                }
            ),
            4
        )

        # payer revokes commits
        payer_state = self.api.call(
            method="mpc_revoke_all",
            params={
                "state": payer_state,
                "secrets": revoke_secrets
            }
        )
        self.assertEqual(
            self.api.call(
                method="mpc_transferred_amount",
                params={
                    "state": payer_state
                }
            ),
            4
        )

    def test_close(self):
        result = self.api.call(
            method="mpc_highest_commit",
            params={
                "state": PAYEE_BEFORE_CLOSE
            }
        )
        self.assertEqual(result, FIXTURES["expected_close_result"])


if __name__ == "__main__":
    unittest.main()
