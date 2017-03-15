import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test.fixtures.params import DP
from counterpartylib.test import util_test
from micropayment_core import keys
from picopayments_hub import api
from picopayments_hub import lib
from micropayment_core import scripts


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = keys.address_from_wif(FUNDING_WIF)


def get_txs(txids):
    return api.getrawtransaction_batch(txhash_list=txids)


@pytest.mark.usefixtures("picopayments_server")
def test_get_hub_liquidity(server_db):

    # confirmed fund
    hub_wif = lib.load_wif()
    hub_address = keys.address_from_wif(hub_wif)
    unsigned_rawtx = api.create_send(**{
        'source': FUNDING_ADDRESS,
        'destination': hub_address,
        'asset': ASSET,
        'quantity': 2000000,
        'regular_dust_size': 2000000
    })
    signed_rawtx = scripts.sign_deposit(get_txs, FUNDING_WIF, unsigned_rawtx)
    api.sendrawtransaction(tx_hex=signed_rawtx)
    assert lib.get_hub_liquidity() == {
        'A7736697071037023001': 0,
        'BTC': 2000000,
        'XCP': 2000000
    }

    # unconfirmed send
    wif = keys.generate_wif("XTN")
    address = keys.address_from_wif(wif)
    unsigned_rawtx = api.create_send(**{
        'source': hub_address,
        'destination': address,
        'asset': ASSET,
        'quantity': 1000000,
        'fee': 1000000
    })
    signed_rawtx = scripts.sign_deposit(get_txs, hub_wif, unsigned_rawtx)
    util_test.insert_unconfirmed_raw_transaction(signed_rawtx, server_db)

    # counts unconfurmed sends
    assert lib.get_hub_liquidity() == {
        'A7736697071037023001': 0,
        'BTC': 0,  # no utxos left
        'XCP': 1000000
    }

    # unconfurmed fund
    unsigned_rawtx = api.create_send(**{
        'source': FUNDING_ADDRESS,
        'destination': hub_address,
        'asset': ASSET,
        'quantity': 2000000,
        'regular_dust_size': 2000000
    })
    signed_rawtx = scripts.sign_deposit(get_txs, FUNDING_WIF, unsigned_rawtx)
    util_test.insert_unconfirmed_raw_transaction(signed_rawtx, server_db)

    # doesnt counts unconfurmed funds
    assert lib.get_hub_liquidity() == {
        'A7736697071037023001': 0,
        'BTC': 0,  # no utxos left
        'XCP': 1000000
    }

    utxos = api.get_unspent_txouts(address=hub_address, unconfirmed=False)
    assert utxos == []
