import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
import os
from pycoin.serialize import b2h
from picopayments_hub import db
from picopayments_hub import api
from picopayments_hub import lib


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_handle_exists():

    def _create_connection(handle):
        db.add_hub_connection({
            "asset": b2h(os.urandom(32)),

            "deposit_max": 0,
            "deposit_min": 0,
            "deposit_ratio": 1.0,
            "expire_max": 0,
            "expire_min": 0,
            "sync_fee": 1,

            "hub_wif": b2h(os.urandom(32)),
            "hub_pubkey": b2h(os.urandom(32)),
            "hub_address": b2h(os.urandom(32)),
            "client_pubkey": b2h(os.urandom(32)),
            "client_address": b2h(os.urandom(32)),
            "secret_hash": b2h(os.urandom(32)),
            "secret_value": b2h(os.urandom(32)),
            "h2c_spend_secret_hash": b2h(os.urandom(32)),
            "handle": handle,
            "hub_rpc_url": b2h(os.urandom(32)),
        })

    _create_connection("a")
    _create_connection("b")

    assert db.handles_exist(["a"])  # test single
    assert db.handles_exist(["b"])  # test single
    assert db.handles_exist(["a", "b"])  # test multiple
    assert db.handles_exist(["c"]) is False  # test missing single
    assert db.handles_exist(["a", "c"]) is False  # test one missing
    assert db.handles_exist(["c", "d"]) is False  # test all missing


@pytest.mark.usefixtures("picopayments_server")
def test_saves_state_revoked(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients
    alice.micro_send(bob.handle, 5)
    alice.sync()

    # load alice c2h_state
    connection = db.hub_connection(handle=alice.handle)
    c2h_state = db.load_channel_state(
        connection["c2h_channel_id"], connection["asset"]
    )

    # revoke c2h commit
    revoke_hashes = api.mpc_revoke_hashes_until(state=c2h_state, quantity=0)
    secrets = [lib.get_secret(h) for h in revoke_hashes]
    updated_c2h_state = api.mpc_revoke_all(state=c2h_state, secrets=secrets)
    assert len(updated_c2h_state["commits_active"]) == 0
    assert len(updated_c2h_state["commits_revoked"]) == 1

    # save updated c2h state
    db.save_channel_state(
        connection["c2h_channel_id"], updated_c2h_state,
        unnotified_revoke_secrets=secrets
    )

    # load updated c2h state
    connection = db.hub_connection(handle=alice.handle)
    saved_c2h_state = db.load_channel_state(
        connection["c2h_channel_id"], connection["asset"]
    )

    assert len(saved_c2h_state["commits_active"]) == 0
    assert len(saved_c2h_state["commits_revoked"]) == 1
    assert updated_c2h_state == saved_c2h_state
