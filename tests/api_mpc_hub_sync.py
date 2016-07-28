import os
import shutil
import json
import unittest
import tempfile
import jsonschema
from picopayments import control
from picopayments import api
from picopayments import exceptions
from counterpartylib.lib.micropayments import scripts


URL = "http://127.0.0.1:14000/api/"


def get_tx_func(txid):
    return api.getrawtransaction(tx_hash=txid)


class TestMpcHubSync(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        fixtures_dir = os.path.join(self.root, "fixtures")
        shutil.copytree("tests/fixtures/sync", fixtures_dir)
        control.initialize([
            "--testnet", "--root={0}".format(fixtures_dir),
            "--cp_url={0}".format(URL)
        ])

    def tearDown(self):
        shutil.rmtree(self.root)

    # FIXME test fails if request made, deposit not made then sync

    def test_poll_updates_xcp(self):
        with open("tests/fixtures/sync/client.json") as fp:
            connection = json.load(fp)
        secret = control.create_secret()
        connection["hub2client_revoke_secrets"].append(secret)
        api.mpc_hub_sync(
            handle=connection["handle"],
            sends=[{
                "payer_handle": connection["handle"],
                "payee_handle": connection["handle"],
                "amount": 1337,
                "token": "deadbeef"
            }],
            commit=None, revokes=None,
            next_revoke_secret_hash=secret["secret_hash"]
        )

    def test_validate_handles_exist(self):

        def func():
            with open("tests/fixtures/sync/client.json") as fp:
                connection = json.load(fp)
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            api.mpc_hub_sync(
                handle=connection["handle"],
                sends=[{
                    "payer_handle": "deadbeef",
                    "payee_handle": connection["handle"],
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                commit=None, revokes=None,
                next_revoke_secret_hash=secret["secret_hash"]
            )

        self.assertRaises(exceptions.HandlesNotFound, func)

    def test_validate_revoke_format(self):

        def func():
            with open("tests/fixtures/sync/client.json") as fp:
                connection = json.load(fp)
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            api.mpc_hub_sync(
                handle=connection["handle"],
                sends=[{
                    "payer_handle": connection["handle"],
                    "payee_handle": connection["handle"],
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                commit=None,
                revokes="invalidformat",
                next_revoke_secret_hash=secret["secret_hash"]
            )

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_validate_commit_format(self):

        def func():
            with open("tests/fixtures/sync/client.json") as fp:
                connection = json.load(fp)
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            api.mpc_hub_sync(
                handle=connection["handle"],
                sends=[{
                    "payer_handle": connection["handle"],
                    "payee_handle": connection["handle"],
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                commit="invalidformat",
                revokes=None,
                next_revoke_secret_hash=secret["secret_hash"]
            )

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_standard_commit(self):
        with open("tests/fixtures/sync/client.json") as fp:
            connection = json.load(fp)

        # create commit
        result = api.mpc_create_commit(
            state={
                "asset": connection["keypair"]["asset"],
                "deposit_script": connection["client2hub_deposit_script"],
                "commits_requested": [],
                "commits_active": [],
                "commits_revoked": []
            },
            quantity=1,
            revoke_secret_hash=connection["client2hub_revoke_secret_hash"],
            delay_time=2
        )
        script = result["commit_script"]

        # sign commit
        rawtx = scripts.sign_created_commit(
            get_tx_func,
            connection["keypair"]["wif"],
            result["tosign"]["commit_rawtx"],
            result["tosign"]["deposit_script"],
        )

        # gen next revoke secret
        next_secret = control.create_secret()
        connection["hub2client_revoke_secrets"].append(next_secret)

        # sync
        api.mpc_hub_sync(
            handle=connection["handle"],
            sends=[{
                "payer_handle": connection["handle"],
                "payee_handle": connection["handle"],
                "amount": 1337,
                "token": "deadbeef"
            }],
            commit={"rawtx": rawtx, "script": script},
            revokes=None,
            next_revoke_secret_hash=next_secret["secret_hash"]
        )
