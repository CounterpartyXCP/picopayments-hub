import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_dublex_transfer(connected_clients):
    alice, bob, charlie, david, eric, fred = connected_clients

    bob_before_status = bob.get_status()
    assert bob_before_status["send_balance"] == 1000000

    alice.micro_send(bob.handle, 1337, "0000")
    assert alice.sync() == []

    bob.micro_send(charlie.handle, 42, "0001")
    assert bob.sync() == [{
        'amount': 1337,
        'payer_handle': alice.handle,
        'token': '0000'
    }]

    bob_after_status = bob.get_status()
    assert bob_after_status["send_balance"] == 1000000 + 1337 - 1 - 42
