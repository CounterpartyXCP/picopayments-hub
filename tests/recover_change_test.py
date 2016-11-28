import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments import cron
from picopayments import api


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_recover_change(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    bob_before_status = bob.get_status()
    assert bob_before_status["balance"] == 1000000

    alice.micro_send(bob.handle, 1337, "0000")
    assert alice.sync() == []

    assert bob.sync() == [{
        'amount': 1337,
        'payer_handle': alice.handle,
        'token': '0000'
    }]

    bob.micro_send(charlie.handle, 42, "0001")
    assert bob.sync() == []

    bob_after_status = bob.get_status()
    assert bob_after_status["balance"] == 1000000 + 1337 - 1 - 42 - 1

    assert bob.close() is not None  # h2c commit txid returned (block created)

    cron.run_all()  # hub close connections cron
    assert len(api.mph_connections()) == 5

    assert len(bob.update()) == 1  # change txid
