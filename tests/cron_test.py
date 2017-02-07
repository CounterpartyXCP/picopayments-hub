import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test import util_test
from picopayments_hub import api
from picopayments_cli.mph import Mph
from picopayments_hub import cron
from picopayments_hub import err
from tests import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_hub_lacks_funds(server_db):
    try:
        auth_wif = util.gen_funded_wif("XCP", 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=auth_wif))
        client.connect(1000000, 65535, asset="XCP")
        cron.fund_deposits()
        assert False
    except err.InsufficientFunds:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_cron_check_for_expire_before_commit(connected_clients, server_db):
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

    # let channel expire
    for i in range(50):
        util_test.create_next_block(server_db)

    rawtxs = alice.update()
    rawtxs = bob.update()
    rawtxs = charlie.update()
    rawtxs = david.update()
    rawtxs = eric.update()
    rawtxs = fred.update()

    rawtxs = cron.recover_funds()
    assert rawtxs is not None
    assert len(rawtxs["change"]) == 0
    assert len(rawtxs["commit"]) == 0
    assert len(rawtxs["revoke"]) == 0
    assert len(rawtxs["payout"]) == 0
    assert len(rawtxs["expire"]) == 5  # missing deposit where commit published

    # let channel expire
    for i in range(50):
        util_test.create_next_block(server_db)

    rawtxs = cron.recover_funds()
    assert rawtxs is not None
    assert len(rawtxs["change"]) == 0
    assert len(rawtxs["commit"]) == 0
    assert len(rawtxs["revoke"]) == 0
    assert len(rawtxs["payout"]) == 0
    assert len(rawtxs["expire"]) == 1  # now recoverable after commit timeout

    balances = alice.get_status()["recv_deposit_balances"]
    assert balances == {"BTC": 0, "XCP": 0}
    address = alice.get_status()["recv_deposit_address"]
    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    assert len(utxos) == 0

    balances = bob.get_status()["recv_deposit_balances"]
    assert balances == {"BTC": 0, "XCP": 0}
    address = bob.get_status()["recv_deposit_address"]
    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    assert len(utxos) == 0

    balances = charlie.get_status()["recv_deposit_balances"]
    assert balances == {"BTC": 0, "XCP": 0}
    address = charlie.get_status()["recv_deposit_address"]
    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    assert len(utxos) == 0

    balances = david.get_status()["recv_deposit_balances"]
    assert balances == {"BTC": 0, "A7736697071037023001": 0}
    address = david.get_status()["recv_deposit_address"]
    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    assert len(utxos) == 0

    balances = eric.get_status()["recv_deposit_balances"]
    assert balances == {"BTC": 0, "A7736697071037023001": 0}
    address = eric.get_status()["recv_deposit_address"]
    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    assert len(utxos) == 0

    balances = fred.get_status()["recv_deposit_balances"]
    assert balances == {"BTC": 0, "A7736697071037023001": 0}
    address = fred.get_status()["recv_deposit_address"]
    utxos = api.get_unspent_txouts(address=address, unconfirmed=False)
    assert len(utxos) == 0

    rawtxs = cron.publish_commits()
    assert rawtxs == []
