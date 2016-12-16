import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments_hub import lib
from picopayments_hub import api
from pycoin.key.validate import is_address_valid
from micropayment_core.keys import address_from_wif
from counterpartylib.test.fixtures.params import DP


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


@pytest.mark.usefixtures("picopayments_server")
def test_get_funding_addresses():
    assets = ["XCP"]
    result = lib.get_funding_addresses(assets)
    assert(assets == list(result.keys()))
    assert(all([
        is_address_valid(a, allowable_netcodes=["XTN"])
        for a in result.values()
    ]))


@pytest.mark.usefixtures("picopayments_server")
def test_validate_read_unknown_asset():
    terms = lib.get_terms(["deadbeef"])
    assert(terms == {})


@pytest.mark.usefixtures("picopayments_server")
def test_no_keys_with_sufficient_asset():

    # create asset
    rawtx = api.create_issuance(
        source=FUNDING_ADDRESS,
        asset="A7736697071037023001",
        quantity=100000000
    )
    api.sendrawtransaction(tx_hex=rawtx)

    # fund server
    for i in range(3):
        addresses = lib.get_funding_addresses(["XCP", "A7736697071037023001"])
        for asset, address in addresses.items():
            rawtx = api.create_send(**{
                'source': FUNDING_ADDRESS,
                'destination': address,
                'asset': asset,
                'quantity': 1000000,
                'regular_dust_size': 1000000
            })
            api.sendrawtransaction(tx_hex=rawtx)

    key = lib.find_key_with_funds("XCP", 1000001, 1000000)
    assert key is None


@pytest.mark.usefixtures("picopayments_server")
def test_no_keys_with_sufficient_btc():

    # create asset
    rawtx = api.create_issuance(
        source=FUNDING_ADDRESS,
        asset="A7736697071037023001",
        quantity=100000000
    )
    api.sendrawtransaction(tx_hex=rawtx)

    # fund server
    for i in range(3):
        addresses = lib.get_funding_addresses(["XCP", "A7736697071037023001"])
        for asset, address in addresses.items():
            rawtx = api.create_send(**{
                'source': FUNDING_ADDRESS,
                'destination': address,
                'asset': asset,
                'quantity': 1000000,
                'regular_dust_size': 1000000
            })
            api.sendrawtransaction(tx_hex=rawtx)

    key = lib.find_key_with_funds("XCP", 1000000, 1000001)
    assert key is None
