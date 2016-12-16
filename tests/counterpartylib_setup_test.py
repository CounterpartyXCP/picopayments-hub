import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test.fixtures.params import DP
from counterpartylib.lib.micropayments.control import get_balance
from counterpartylib.lib.api import dispatcher
from micropayment_core.keys import address_from_wif
from micropayment_core.keys import generate_wif
from picopayments_hub import api


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


ALICE_WIF = DP["addresses"][0][2]
ALICE_ADDRESS = address_from_wif(ALICE_WIF)
BOB_WIF = generate_wif(netcode="XTN")
BOB_ADDRESS = address_from_wif(BOB_WIF)


@pytest.mark.usefixtures("picopayments_server")
def test_commit_tx_alpha():

    rawtx = api.create_send(**{
        'source': ALICE_ADDRESS,
        'destination': BOB_ADDRESS,
        'asset': 'XCP',
        'quantity': 33,
        'regular_dust_size': 42
    })

    asset_balance, btc_balance = get_balance(dispatcher, "XCP", BOB_ADDRESS)
    assert asset_balance == 0
    assert btc_balance == 0

    api.sendrawtransaction(tx_hex=rawtx)

    asset_balance, btc_balance = get_balance(dispatcher, "XCP", BOB_ADDRESS)
    assert asset_balance == 33
    assert btc_balance == 42


@pytest.mark.usefixtures("picopayments_server")
def test_commit_tx_beta():

    rawtx = api.create_send(**{
        'source': ALICE_ADDRESS,
        'destination': BOB_ADDRESS,
        'asset': 'XCP',
        'quantity': 13,
        'regular_dust_size': 33
    })

    asset_balance, btc_balance = get_balance(dispatcher, "XCP", BOB_ADDRESS)
    assert asset_balance == 0
    assert btc_balance == 0

    api.sendrawtransaction(tx_hex=rawtx)

    asset_balance, btc_balance = get_balance(dispatcher, "XCP", BOB_ADDRESS)
    assert asset_balance == 13
    assert btc_balance == 33
