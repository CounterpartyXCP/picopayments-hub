import os
import shutil
import json
import unittest
import tempfile
import jsonschema
from picopayments import control
from picopayments import api
from picopayments import exceptions


URL = "http://127.0.0.1:14000/api/"


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

    def test_poll_updates_xcp(self):
        connection = json.load(open("tests/fixtures/sync/client.json"))
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
            connection = json.load(open("tests/fixtures/sync/client.json"))
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
            connection = json.load(open("tests/fixtures/sync/client.json"))
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
            connection = json.load(open("tests/fixtures/sync/client.json"))
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
