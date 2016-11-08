import os
import json
import shutil
import unittest
import tempfile
import jsonschema
from picopayments import api
from picopayments_client import auth
from picopayments import lib
from picopayments import etc
from picopayments import srv
from picopayments import err
from micropayment_core import keys
from picopayments_client.mph import Mph
from tests.mock import MockAPI


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

    def _create_commit(self, client, quantity):
        result = client.create_signed_commit(
            client.client_wif, client.c2h_state, quantity,
            client.c2h_next_revoke_secret_hash, client.c2h_commit_delay_time
        )
        client.c2h_state = result["state"]
        return result["commit"]

    @unittest.skip("FIXME")
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
            params = auth.sign_json(params, keys.wif_to_privkey(wif))
            api.mph_sync(**params)

        self.assertRaises(err.PaymentExceedsSpendable, func)

    def test_pubkey_missmatch(self):

        def func():
            secret = lib.create_secret()
            connection = self.data["connections"]["alpha"]
            handle = connection["handle"]
            wif = keys.generate_wif(netcode=etc.netcode)
            params = {
                "handle": handle,
                "sends": [],
                "commit": None,
                "revokes": None,
                "next_revoke_secret_hash": secret["secret_hash"]
            }
            params = auth.sign_json(params, keys.wif_to_privkey(wif))
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
            params = auth.sign_json(params, keys.wif_to_privkey(wif))
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
            params = auth.sign_json(params, keys.wif_to_privkey(wif))
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
            params = auth.sign_json(params, keys.wif_to_privkey(wif))
            api.mph_sync(**params)

        self.assertRaises(jsonschema.exceptions.ValidationError, func)

    @unittest.skip("FIXME")
    def test_standard_commit(self):
        quantity = 5
        client = Mph.deserialize(data=self.data["connections"]["alpha"],
                                 api_cls=MockAPI)
        sync_fee = client.channel_terms["sync_fee"]
        commit = self._create_commit(client, quantity + sync_fee)

        h2c_next_revoke_secret_hash = client._gen_secret()
        client._add_to_commits_requested(h2c_next_revoke_secret_hash)
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
        params = auth.sign_json(params, keys.wif_to_privkey(client.client_wif))
        result = api.mph_sync(**params)

        self.assertEqual(result["receive"], [{
            "payer_handle": client.handle,
            "token": "deadbeef",
            "amount": 5
        }])
        self.assertIsNotNone(result["commit"])

    @unittest.skip("FIXME")
    def test_repeated_transfer(self):
        alpha_data = self.data["connections"]["alpha"]
        alpha_client = Mph.deserialize(data=alpha_data, api_cls=MockAPI)
        beta_data = self.data["connections"]["beta"]
        beta_client = Mph.deserialize(data=beta_data, api_cls=MockAPI)

        # ensure beta has one notified commit
        alpha_client.micro_send(beta_client.handle, 3)
        alpha_client.sync()
        beta_client.sync()

        # ensure unnotified commit is replaced
        alpha_client.micro_send(beta_client.handle, 5)
        alpha_client.sync()
        alpha_client.micro_send(beta_client.handle, 7)
        alpha_client.sync()
        beta_client.sync()

        # check balances
        alpha_status = alpha_client.get_status()
        beta_status = beta_client.get_status()
        self.assertEqual(alpha_status["balance"], 1593 - 18)
        self.assertEqual(beta_status["balance"], 1337 + 13)

    @unittest.skip("FIXME")
    def test_asset_missmatch(self):

        def func():
            # create alice XCP connection
            auth_wif = self.data["funded"]["epsilon"]["wif"]
            asset = self.data["funded"]["epsilon"]["asset"]
            alice = Mph(MockAPI(
                auth_wif=auth_wif,
                verify_ssl_cert=False
            ))
            txid = alice.connect(1337, 65535, asset=asset, dryrun=True)
            self.assertIsNotNone(txid)

            # load bob A14456548018133352000 connection
            quantity = 5
            bob = Mph.deserialize(data=self.data["connections"]["alpha"],
                                  api_cls=MockAPI)
            sync_fee = bob.channel_terms["sync_fee"]
            commit = self._create_commit(bob, quantity + sync_fee)

            h2c_next_revoke_secret_hash = bob._gen_secret()
            bob._add_to_commits_requested(h2c_next_revoke_secret_hash)

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
            privkey = keys.wif_to_privkey(bob.client_wif)
            params = auth.sign_json(params, privkey)
            api.mph_sync(**params)

        self.assertRaises(err.AssetMissmatch, func)

    @unittest.skip("FIXME")
    def test_payment_exceeds_receivable(self):

        def func():
            alice = Mph.deserialize(
                data=self.data["connections"]["beta"], api_cls=MockAPI)

            # load bob A14456548018133352000 connection
            quantity = 1338
            bob = Mph.deserialize(data=self.data["connections"]["alpha"],
                                  api_cls=MockAPI)
            sync_fee = bob.channel_terms["sync_fee"]
            commit = self._create_commit(bob, quantity + sync_fee)

            h2c_next_revoke_secret_hash = bob._gen_secret()
            bob._add_to_commits_requested(h2c_next_revoke_secret_hash)
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
            privkey = keys.wif_to_privkey(bob.client_wif)
            params = auth.sign_json(params, privkey)
            api.mph_sync(**params)

        self.assertRaises(err.PaymentExceedsReceivable, func)

    def test_payer_deposit_expired(self):

        def func():
            quantity = 5
            client = Mph.deserialize(
                data=self.data["connections"]["eta"], api_cls=MockAPI)
            sync_fee = client.channel_terms["sync_fee"]
            commit = self._create_commit(client, quantity + sync_fee)
            h2c_next_revoke_secret_hash = client._gen_secret()
            client._add_to_commits_requested(h2c_next_revoke_secret_hash)
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
            privkey = keys.wif_to_privkey(client.client_wif)
            params = auth.sign_json(params, privkey)
            api.mph_sync(**params)

        self.assertRaises(err.DepositExpired, func)

    def test_payee_deposit_expired(self):

        def func():
            alice = Mph.deserialize(
                data=self.data["connections"]["alpha"], api_cls=MockAPI
            )
            bob = Mph.deserialize(data=self.data["connections"]["eta"],
                                  api_cls=MockAPI)
            quantity = 5
            sync_fee = alice.channel_terms["sync_fee"]
            commit = self._create_commit(alice, quantity + sync_fee)
            h2c_next_revoke_secret_hash = alice._gen_secret()
            alice._add_to_commits_requested(h2c_next_revoke_secret_hash)
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
            privkey = keys.wif_to_privkey(alice.client_wif)
            params = auth.sign_json(params, privkey)
            api.mph_sync(**params)

        self.assertRaises(err.DepositExpired, func)


if __name__ == "__main__":
    unittest.main()
