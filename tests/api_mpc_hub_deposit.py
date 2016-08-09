import os
import time
import shutil
import unittest
import tempfile
from pycoin.serialize import b2h
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments.scripts import compile_deposit_script
from picopayments import control
from picopayments import exceptions
import jsonschema
from picopayments.main import main
from multiprocessing import Process
from picopayments import rpc


HOST = "127.0.0.1"
PORT = "15000"
URL = "https://127.0.0.1:15000/api/"
CP_URL = "http://127.0.0.1:14000/api/"


DEPOSIT_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "deposit_script": {"type": "string"},
        "next_revoke_secret_hash": {"type": "string"},
        "signature": {"type": "string"},
        "pubkey": {"type": "string"},
    },
    "required": [
        "deposit_script", "next_revoke_secret_hash", "signature", "pubkey"
    ],
    "additionalProperties": False
}


class TestMpcHubDeposit(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="picopayments_test_")
        self.server = Process(target=main, args=([
            "--testnet",
            "--root={0}".format(self.root),
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

    def test_standard_usage_xcp(self):

        asset = "XCP"
        client_key = control.create_key(asset, netcode="XTN")
        client_pubkey = client_key["pubkey"]

        hub2client_spend_secret = util.b2h(os.urandom(32))
        hub2client_spend_secret_hash = util.hash160hex(hub2client_spend_secret)

        result = rpc.call(
            url=URL,
            method="mpc_hub_request",
            params={
                "asset": asset,
                "spend_secret_hash": hub2client_spend_secret_hash
            },
            verify_ssl_cert=False,  # only needed for encryption
            authentication_wif=client_key["wif"]
        )
        handle = result["handle"]
        hub_pubkey = result["pubkey"]
        client2hub_spend_secret_hash = result["spend_secret_hash"]

        client2hub_deposit_script = b2h(compile_deposit_script(
            client_pubkey, hub_pubkey, client2hub_spend_secret_hash, 1337
        ))

        next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        result = rpc.call(
            url=URL,
            method="mpc_hub_deposit",
            params={
                "handle": handle,
                "deposit_script": client2hub_deposit_script,
                "next_revoke_secret_hash": next_revoke_secret_hash
            },
            verify_ssl_cert=False,  # only needed for encryption
            authentication_wif=client_key["wif"]
        )
        self.assertIsNotNone(result)
        jsonschema.validate(result, DEPOSIT_RESULT_SCHEMA)

    def test_validate_deposit_not_already_given(self):

        def func():

            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            client_pubkey = client_key["pubkey"]

            hub2client_spend_secret = util.b2h(os.urandom(32))
            hub2client_spend_secret_hash = util.hash160hex(
                hub2client_spend_secret
            )

            result = rpc.call(
                url=URL,
                method="mpc_hub_request",
                params={
                    "asset": asset,
                    "spend_secret_hash": hub2client_spend_secret_hash
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )
            handle = result["handle"]
            hub_pubkey = result["pubkey"]
            client2hub_spend_secret_hash = result["spend_secret_hash"]

            client2hub_deposit_script = b2h(compile_deposit_script(
                client_pubkey, hub_pubkey, client2hub_spend_secret_hash, 1337
            ))

            # submit deposit
            next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            result = rpc.call(
                url=URL,
                method="mpc_hub_deposit",
                params={
                    "handle": handle,
                    "deposit_script": client2hub_deposit_script,
                    "next_revoke_secret_hash": next_revoke_secret_hash
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )
            self.assertIsNotNone(result)

            # resubmit deposit
            next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            result = rpc.call(
                url=URL,
                method="mpc_hub_deposit",
                params={
                    "handle": handle,
                    "deposit_script": client2hub_deposit_script,
                    "next_revoke_secret_hash": next_revoke_secret_hash
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(exceptions.DepositAlreadyGiven, func)

    def test_validate_handle_exists(self):

        def func():

            asset = "XCP"
            client_key = control.create_key(asset, netcode="XTN")
            next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
            client2hub_deposit_script = util.b2h(os.urandom(32)),
            rpc.call(
                url=URL,
                method="mpc_hub_deposit",
                params={
                    "handle": "deadbeef",
                    "deposit_script": client2hub_deposit_script,
                    "next_revoke_secret_hash": next_revoke_secret_hash
                },
                verify_ssl_cert=False,  # only needed for encryption
                authentication_wif=client_key["wif"]
            )

        self.assertRaises(Exception, func)
        # self.assertRaises(exceptions.HandleNotFound, func)


if __name__ == "__main__":
    unittest.main()
