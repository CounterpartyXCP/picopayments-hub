import os
import json
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments import auth
from picopayments import lib
from picopayments import etc
from picopayments import srv
from picopayments import err
from picopayments import Client
from counterpartylib.lib.micropayments import util


etc.call_local_process = True
CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestMpcHubSync(unittest.TestCase):

    # FIXME test fails if request made, deposit not made then sync

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ], serve=False)
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_payment_exceeds_spendable(self):

        def func():
            secret = lib.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [{
                    "payee_handle": handle,
                    "amount": 31337,
                    "token": "deadbeef"
                }],
                "commit": None,
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mph_sync(**params)

        self.assertRaises(err.PaymentExceedsSpendable, func)

    def test_pubkey_missmatch(self):

        def func():
            secret = lib.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = util.random_wif(netcode=etc.netcode)
            params = {
                "handle": handle,
                "sends": [],
                "commit": None,
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mph_sync(**params)

        self.assertRaises(err.ClientPubkeyMissmatch, func)

    def test_validate_handles_exist(self):

        def func():
            secret = lib.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [{
                    "payee_handle": "deadbeef",
                    "amount": 1337,
                    "token": "deadbeef"
                }],
                "commit": None,
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mph_sync(**params)

        self.assertRaises(err.HandlesNotFound, func)

    def test_validate_revoke_format(self):

        def func():
            secret = lib.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [],
                "commit": None,
                "revokes": "invalidformat",
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mph_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_validate_commit_format(self):

        def func():
            secret = lib.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = connection["client_wif"]
            params = {
                "handle": handle,
                "sends": [],
                "commit": "invalidformat",
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, wif)
            api.mph_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    def test_standard_commit(self):
        quantity = 5
        client = Client.deserialize(self.data["connections"]["alpha"])
        sync_fee = client.channel_terms["sync_fee"]
        commit = client.create_commit(quantity + sync_fee)
        h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
        h2c_next_revoke_secret_hash = util.hash160hex(
            h2c_next_revoke_secret_value
        )
        params = {
            "handle": client.handle,
            "sends": [{
                "payee_handle": client.handle,
                "amount": quantity,
                "token": "deadbeef"
            }],
            "commit": commit,
            "revokes": None,
            "next_revoke_secret_hash": h2c_next_revoke_secret_hash
        }
        params = auth.sign_json(params, client.client_wif)
        result = api.mph_sync(**params)

        self.assertEqual(result["receive"], [{
            "payer_handle": client.handle,
            "token": "deadbeef",
            "amount": 5
        }])
        self.assertIsNotNone(result["commit"])

    def test_asset_missmatch(self):

        def func():
            # create alice XCP connection
            auth_wif = self.data["funded"]["epsilon"]["wif"]
            asset = self.data["funded"]["epsilon"]["asset"]
            alice = Client(
                auth_wif=auth_wif,
                verify_ssl_cert=False
            )
            txid = alice.connect(1337, 65535, asset=asset, publish_tx=False)
            self.assertIsNotNone(txid)

            # load bob A14456548018133352000 connection
            quantity = 5
            bob = Client.deserialize(self.data["connections"]["alpha"])
            sync_fee = bob.channel_terms["sync_fee"]
            commit = bob.create_commit(quantity + sync_fee)
            h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
            h2c_next_revoke_secret_hash = util.hash160hex(
                h2c_next_revoke_secret_value
            )
            params = {
                "handle": bob.handle,
                "sends": [{
                    "payee_handle": alice.handle,
                    "amount": quantity,
                    "token": "deadbeef"
                }],
                "commit": commit,
                "revokes": None,
                "next_revoke_secret_hash": h2c_next_revoke_secret_hash
            }
            params = auth.sign_json(params, bob.client_wif)
            api.mph_sync(**params)

        self.assertRaises(err.AssetMissmatch, func)

    def test_payment_exceeds_receivable(self):

        def func():
            alice = Client.deserialize(self.data["connections"]["beta"])

            # load bob A14456548018133352000 connection
            quantity = 1338
            bob = Client.deserialize(self.data["connections"]["alpha"])
            sync_fee = bob.channel_terms["sync_fee"]
            commit = bob.create_commit(quantity + sync_fee)
            h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
            h2c_next_revoke_secret_hash = util.hash160hex(
                h2c_next_revoke_secret_value
            )
            params = {
                "handle": bob.handle,
                "sends": [{
                    "payee_handle": alice.handle,
                    "amount": quantity,
                    "token": "deadbeef"
                }],
                "commit": commit,
                "revokes": None,
                "next_revoke_secret_hash": h2c_next_revoke_secret_hash
            }
            params = auth.sign_json(params, bob.client_wif)
            api.mph_sync(**params)

        self.assertRaises(err.PaymentExceedsReceivable, func)

    def test_payer_deposit_expired(self):

        def func():
            quantity = 5
            client = Client.deserialize(self.data["connections"]["eta"])
            sync_fee = client.channel_terms["sync_fee"]
            commit = client.create_commit(quantity + sync_fee)
            h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
            h2c_next_revoke_secret_hash = util.hash160hex(
                h2c_next_revoke_secret_value
            )
            params = {
                "handle": client.handle,
                "sends": [{
                    "payee_handle": client.handle,
                    "amount": quantity,
                    "token": "deadbeef"
                }],
                "commit": commit,
                "revokes": None,
                "next_revoke_secret_hash": h2c_next_revoke_secret_hash
            }
            params = auth.sign_json(params, client.client_wif)
            api.mph_sync(**params)

        self.assertRaises(err.DepositExpired, func)

    def test_payee_deposit_expired(self):

        def func():
            alice = Client.deserialize(self.data["connections"]["alpha"])
            bob = Client.deserialize(self.data["connections"]["eta"])
            quantity = 5
            sync_fee = alice.channel_terms["sync_fee"]
            commit = alice.create_commit(quantity + sync_fee)
            h2c_next_revoke_secret_value = util.b2h(os.urandom(32))
            h2c_next_revoke_secret_hash = util.hash160hex(
                h2c_next_revoke_secret_value
            )
            params = {
                "handle": alice.handle,
                "sends": [{
                    "payee_handle": bob.handle,
                    "amount": quantity,
                    "token": "deadbeef"
                }],
                "commit": commit,
                "revokes": None,
                "next_revoke_secret_hash": h2c_next_revoke_secret_hash
            }
            params = auth.sign_json(params, alice.client_wif)
            api.mph_sync(**params)

        self.assertRaises(err.DepositExpired, func)


if __name__ == "__main__":
    unittest.main()
