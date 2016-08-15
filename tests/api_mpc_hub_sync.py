import os
import json
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments import auth
from picopayments import control
from picopayments import cli
from picopayments import exceptions
from counterpartylib.lib.micropayments import scripts


CP_URL = "http://127.0.0.1:14000/api/"


def get_tx_func(txid):
    return api.getrawtransaction(tx_hash=txid)


def connection_initial_states(connection):
    send = {
        "asset": connection["keypair"]["asset"],
        "deposit_script": connection["client2hub_deposit_script"],
        "commits_requested": [],
        "commits_active": [],
        "commits_revoked": [],
    }
    recv = {
        "asset": connection["keypair"]["asset"],
        "deposit_script": connection["hub2client_deposit_script"],
        "commits_requested": [],
        "commits_active": [],
        "commits_revoked": [],
    }
    return send, recv


class TestMpcHubSync(unittest.TestCase):

    # FIXME test fails if request made, deposit not made then sync

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", basedir)
        control.initialize(cli.parse([
            "--testnet",
            "--basedir={0}".format(basedir),
            "--cp_url={0}".format(CP_URL)
        ]))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _test_validate_handles_exist(self):

        def func():
            with open("test_basedir/client.json") as fp:
                connection = json.load(fp)
            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            params = {
                "handle": connection["handle"],
                "sends": [{
                    "payer_handle": "deadbeef",
                    "payee_handle": connection["handle"],
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                "commit": None,
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, client_key["wif"])
            api.mpc_hub_sync(**params)

        self.assertRaises(exceptions.HandlesNotFound, func)

    def _test_validate_revoke_format(self):

        def func():
            with open("test_basedir/client.json") as fp:
                connection = json.load(fp)
            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            params = {
                "handle": connection["handle"],
                "sends": [{
                    "payer_handle": connection["handle"],
                    "payee_handle": connection["handle"],
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                "commit": None,
                "revokes": "invalidformat",
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, client_key["wif"])
            api.mpc_hub_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def _test_validate_commit_format(self):

        def func():
            with open("test_basedir/client.json") as fp:
                connection = json.load(fp)
            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            params = {
                "handle": connection["handle"],
                "sends": [{
                    "payer_handle": connection["handle"],
                    "payee_handle": connection["handle"],
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                "commit": "invalidformat",
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, client_key["wif"])
            api.mpc_hub_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_standard_commit(self):
        with open("test_basedir/client.json") as fp:
            connection = json.load(fp)

        send_amount = 5

        # create commit
        send_state, recv_state = connection_initial_states(connection)
        revoke_secret_hash = connection["client2hub_revoke_secret_hash"]
        params = {
            "state": send_state,
            "quantity": connection["terms"]["fee_sync"] + send_amount,
            "revoke_secret_hash": revoke_secret_hash,
            "delay_time": 2
        }
        result = api.mpc_create_commit(**params)
        script = result["commit_script"]

        # sign commit
        rawtx = scripts.sign_created_commit(
            get_tx_func,
            connection["keypair"]["wif"],
            result["tosign"]["commit_rawtx"],
            result["tosign"]["deposit_script"],
        )

        asset = "XCP"
        client_key = control.create_key(asset, netcode="XTN")

        # gen next revoke secret
        next_secret = control.create_secret()
        connection["hub2client_revoke_secrets"].append(next_secret)

        # sync send payment to self
        params = {
            "handle": connection["handle"],
            "sends": [{
                "payer_handle": connection["handle"],
                "payee_handle": connection["handle"],
                "amount": send_amount,
                "token": "deadbeef"
            }],
            "commit": {"rawtx": rawtx, "script": script},
            "revokes": None,
            "next_revoke_secret_hash": next_secret["secret_hash"]
        }
        params = auth.sign_json(params, client_key["wif"])
        result = api.mpc_hub_sync(**params)

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
