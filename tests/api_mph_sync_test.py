import tempfile
import pytest
import jsonschema

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test import util_test
from picopayments_hub import lib
from picopayments_hub import api
from picopayments_hub import err
from picopayments_hub import etc
from picopayments_cli import auth
from micropayment_core import keys


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


def _create_commit(client, quantity):
    result = client.create_signed_commit(
        client.api.auth_wif, client.c2h_state, quantity,
        client.c2h_next_revoke_secret_hash, client.c2h_commit_delay_time
    )
    client.c2h_state = result["state"]
    return result["commit"]


@pytest.mark.usefixtures("picopayments_server")
def test_pubkey_missmatch(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:
        secret = lib.create_secret()
        handle = alice.handle
        wif = keys.generate_wif(netcode=etc.netcode)
        params = {
            "handle": handle,
            "sends": [],
            "commit": None,
            "revokes": None,
            "next_revoke_secret_hash": secret["secret_hash"]
        }
        params = auth.sign_json(params, wif)
        api.mph_sync(**params)
        assert False
    except err.ClientPubkeyMissmatch:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_validate_handles_exist(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:
        secret = lib.create_secret()
        params = {
            "handle": alice.handle,
            "sends": [{
                "payee_handle": "deadbeef",
                "amount": 1337,
                "token": "deadbeef"
            }],
            "commit": None,
            "revokes": None,
            "next_revoke_secret_hash": secret["secret_hash"]
        }
        api.mph_sync(**auth.sign_json(params, alice.api.auth_wif))
        assert False
    except err.HandlesNotFound:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_validate_revoke_format(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:
        secret = lib.create_secret()
        params = {
            "handle": alice.handle,
            "sends": [],
            "commit": None,
            "revokes": "invalidformat",
            "next_revoke_secret_hash": secret["secret_hash"]
        }
        params = auth.sign_json(params, alice.api.auth_wif)
        api.mph_sync(**params)
        assert False
    except jsonschema.exceptions.ValidationError:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_validate_commit_format(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:
        secret = lib.create_secret()
        params = {
            "handle": alice.handle,
            "sends": [],
            "commit": "invalidformat",
            "revokes": None,
            "next_revoke_secret_hash": secret["secret_hash"]
        }
        params = auth.sign_json(params, alice.api.auth_wif)
        api.mph_sync(**params)
        assert False
    except jsonschema.exceptions.ValidationError:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_standard_commit(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    quantity = 5
    sync_fee = alice.channel_terms["sync_fee"]
    commit = _create_commit(alice, quantity + sync_fee)

    h2c_next_revoke_secret_hash = alice._gen_secret()
    alice._add_to_commits_requested(h2c_next_revoke_secret_hash)
    params = {
        "handle": alice.handle,
        "sends": [{
            "payee_handle": alice.handle,
            "amount": quantity,
            "token": "deadbeef"
        }],
        "commit": commit,
        "revokes": None,
        "next_revoke_secret_hash": h2c_next_revoke_secret_hash
    }
    params = auth.sign_json(params, alice.api.auth_wif)
    result = api.mph_sync(**params)

    assert result["receive"] == [{
        "payer_handle": alice.handle,
        "token": "deadbeef",
        "amount": 5
    }]
    assert result["commit"] is not None


@pytest.mark.usefixtures("picopayments_server")
def test_repeated_micro_send(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    alice.micro_send(bob.handle, 5)
    alice.micro_send(bob.handle, 7)
    alice.sync()
    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000 - 13

    bob.sync()
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000 + 11


@pytest.mark.usefixtures("picopayments_server")
def test_repeated_transfer(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    alice.micro_send(bob.handle, 5)
    alice.sync()
    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000 - 5 - 1

    bob.sync()
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000 + 5 - 1

    alice.micro_send(bob.handle, 7)
    alice.sync()
    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000 - 5 - 1 - 7 - 1

    bob.sync()
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000 + 5 - 1 + 7 - 1


@pytest.mark.usefixtures("picopayments_server")
def test_repeated_unnotified_transfer(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    # ensure unnotified commit is replaced
    alice.micro_send(bob.handle, 5)
    alice.sync()

    alice.micro_send(bob.handle, 7)
    alice.sync()
    bob.sync()

    # check balances
    alice_status = alice.get_status()
    bob_status = bob.get_status()
    assert alice_status["send_balance"] == 1000000 - 6 - 8
    assert bob_status["send_balance"] == 1000000 + 5 + 7 - 1


@pytest.mark.usefixtures("picopayments_server")
def test_asset_missmatch(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    try:
        quantity = 5
        sync_fee = david.channel_terms["sync_fee"]
        commit = _create_commit(david, quantity + sync_fee)

        h2c_next_revoke_secret_hash = david._gen_secret()
        david._add_to_commits_requested(h2c_next_revoke_secret_hash)

        params = {
            "handle": david.handle,
            "sends": [{
                "payee_handle": alice.handle,
                "amount": quantity,
                "token": "deadbeef"
            }],
            "commit": commit,
            "revokes": None,
            "next_revoke_secret_hash": h2c_next_revoke_secret_hash
        }

        params = auth.sign_json(params, david.api.auth_wif)
        api.mph_sync(**params)

        assert False
    except err.AssetMissmatch:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_send_max(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000

    alice.micro_send(bob.handle, 999999, "f483")
    alice.sync()
    assert bob.sync() == [{
        "payer_handle": alice.handle,
        "amount": 999999,
        "token": "f483"
    }]

    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 0
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1999998


@pytest.mark.usefixtures("picopayments_server")
def test_send_exceeds_max(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:
        secret = lib.create_secret()
        params = {
            "handle": alice.handle,
            "sends": [{
                "payee_handle": bob.handle,
                "amount": 1000000,
                "token": "deadbeef"
            }],
            "commit": None,
            "revokes": None,
            "next_revoke_secret_hash": secret["secret_hash"]
        }
        params = auth.sign_json(params, alice.api.auth_wif)
        api.mph_sync(**params)
        assert False
    except err.PaymentExceedsSpendable:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_receive_max(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000
    charlie_status = charlie.get_status()
    assert charlie_status["send_balance"] == 1000000

    alice.micro_send(charlie.handle, 500000)
    alice.sync()

    bob.micro_send(charlie.handle, 500000)
    bob.sync()

    charlie.sync()
    charlie_status = charlie.get_status()
    assert charlie_status["send_balance"] == 1999999


@pytest.mark.usefixtures("picopayments_server")
def test_receive_max_exceeded(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000
    charlie_status = charlie.get_status()
    assert charlie_status["send_balance"] == 1000000

    try:
        alice.micro_send(charlie.handle, 500000)
        alice.sync()

        bob.micro_send(charlie.handle, 500001)
        bob.sync()

        assert False
    except err.PaymentExceedsReceivable:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_payer_deposit_expired(connected_clients, server_db):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:

        # let client deposit expire
        c2h_deposit_ttl = 9999999999999999
        while c2h_deposit_ttl > 0:
            util_test.create_next_block(server_db)
            status = alice.get_status(clearance=0)
            c2h_deposit_ttl = status["send_deposit_ttl"]

        # attempt to transfer funds
        alice.micro_send(bob.handle, 1337)
        alice.sync()

        assert False
    except err.DepositExpired:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_payee_deposit_expired(connected_clients, server_db):
    alice, bob, charlie, david, eric, fred = connected_clients
    try:

        # let client deposit expire
        c2h_deposit_ttl = 9999999999999999
        while c2h_deposit_ttl > 0:
            util_test.create_next_block(server_db)
            status = alice.get_status(clearance=0)
            c2h_deposit_ttl = status["send_deposit_ttl"]

        # attempt to transfer funds
        bob.micro_send(alice.handle, 1337)
        bob.sync()

        assert False
    except err.DepositExpired:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_c2h_revoke_commit(connected_clients, server_db):
    alice, bob, charlie, david, eric, fred = connected_clients

    # send funds to bob
    alice.micro_send(bob.handle, 5)
    alice.sync()
    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000 - 5 - 1

    # bob received funds
    bob.sync()
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000 + 5 - 1

    # return funds to alice
    bob.micro_send(alice.handle, 10)
    bob.sync()
    bob_status = bob.get_status()
    assert bob_status["send_balance"] == 1000000 + 5 - 1 - 10 - 1

    # check alice received returned funds
    alice.sync()
    alice_status = alice.get_status()
    assert alice_status["send_balance"] == 1000000 - 5 - 1 + 10 - 1


@pytest.mark.usefixtures("picopayments_server")
def test_h2c_revoke_commit(connected_clients, server_db):
    alice, bob, charlie, david, eric, fred = connected_clients
