import time
import os
import shutil
import json
import unittest
import tempfile
import jsonschema
from picopayments import control
from picopayments import exceptions
from counterpartylib.lib.micropayments import scripts
from picopayments.main import main
from multiprocessing import Process
from picopayments import rpc


HOST = "127.0.0.1"
PORT = "15000"
URL = "https://127.0.0.1:15000/api/"
CP_URL = "http://127.0.0.1:14000/api/"


def get_tx_func(txid):
    return rpc.call(
        url=URL,
        method="getrawtransaction",
        params={"tx_hash": txid},
        verify_ssl_cert=False  # only needed for encryption
    )


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

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        fixtures_dir = os.path.join(self.root, "fixtures")
        shutil.copytree("tests/fixtures/sync", fixtures_dir)
        self.server = Process(target=main, args=([
            "--testnet",
            "--root={0}".format(fixtures_dir),
            "--host={0}".format(HOST),
            "--port={0}".format(PORT),
            "--cp_url={0}".format(CP_URL)
        ],))
        self.server.start()
        time.sleep(5)  # wait until server started

    def tearDown(self):
        self.server.terminate()
        self.server.join()
        shutil.rmtree(self.root)

    # FIXME test fails if request made, deposit not made then sync

    def _test_validate_handles_exist(self):

        def func():
            with open("tests/fixtures/sync/client.json") as fp:
                connection = json.load(fp)
            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            rpc.call(
                url=URL,
                method="mpc_hub_sync",
                params={
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
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(exceptions.HandlesNotFound, func)

    def _test_validate_revoke_format(self):

        def func():
            with open("tests/fixtures/sync/client.json") as fp:
                connection = json.load(fp)
            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            rpc.call(
                url=URL,
                method="mpc_hub_sync",
                params={
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
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def _test_validate_commit_format(self):

        def func():
            with open("tests/fixtures/sync/client.json") as fp:
                connection = json.load(fp)
            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            secret = control.create_secret()
            connection["hub2client_revoke_secrets"].append(secret)
            rpc.call(
                url=URL,
                method="mpc_hub_sync",
                params={
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
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_standard_commit(self):
        with open("tests/fixtures/sync/client.json") as fp:
            connection = json.load(fp)

        send_amount = 5

        # create commit
        send_state, recv_state = connection_initial_states(connection)
        revoke_secret_hash = connection["client2hub_revoke_secret_hash"]
        result = rpc.call(
            url=URL,
            method="mpc_create_commit",
            params={
                "state": send_state,
                "quantity": connection["terms"]["fee_sync"] + send_amount,
                "revoke_secret_hash": revoke_secret_hash,
                "delay_time": 2
            },
            verify_ssl_cert=False  # only needed for encryption
        )
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
        result = rpc.call(
            url=URL,
            method="mpc_hub_sync",
            params={
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
            },
            verify_ssl_cert=False,  # only needed for encryption
            authentication_wif=client_key["wif"]
        )
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
