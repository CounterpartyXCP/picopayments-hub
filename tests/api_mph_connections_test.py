import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test.fixtures.params import DP
from micropayment_core.keys import address_from_wif
from picopayments_client.mph import Mph
from picopayments import lib
from tests import util
import jsonschema
from picopayments import api
from picopayments_client import auth


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)
CONNECTION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "handle": {"type": "string"},
        "c2h_deposit_script": {"type": "string"},
        "h2c_deposit_script": {"type": "string"},
        "pubkey": {"type": "string"},
        "signature": {"type": "string"},
        "client_url": {"type": ["string", "null"]},
    },
    "required": [
        "asset", "handle", "client_url",
        "c2h_deposit_script", "h2c_deposit_script",
        "pubkey", "signature"
    ],
    "additionalProperties": False
}


@pytest.mark.usefixtures("picopayments_server")
def test_all(server_db):

    # fund server
    for i in range(3):
        address = lib.get_funding_addresses([ASSET])[ASSET]
        rawtx = api.create_send(**{
            'source': FUNDING_ADDRESS,
            'destination': address,
            'asset': ASSET,
            'quantity': 1000000,
            'regular_dust_size': 1000000
        })
        api.sendrawtransaction(tx_hex=rawtx)

    # connect clients
    assert len(api.mph_connections()) == 0
    clients = []
    for i in range(3):
        bob_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=bob_wif))
        client.connect(1000000, 65535, asset=ASSET)
        clients.append(client)

    connections = api.mph_connections()
    assert len(connections) == 3
    for connection in connections:
        jsonschema.validate(connection, CONNECTION_RESULT_SCHEMA)
        auth.verify_json(connection)
        # FIXME validate pubkey matches hub deposit script payer


@pytest.mark.usefixtures("picopayments_server")
def test_filters_assets():

    # fund server
    for i in range(3):
        address = lib.get_funding_addresses([ASSET])[ASSET]
        rawtx = api.create_send(**{
            'source': FUNDING_ADDRESS,
            'destination': address,
            'asset': ASSET,
            'quantity': 1000000,
            'regular_dust_size': 1000000
        })
        api.sendrawtransaction(tx_hex=rawtx)

    # connect clients
    assert len(api.mph_connections()) == 0
    clients = []
    for i in range(3):
        bob_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=bob_wif))
        client.connect(1000000, 65535, asset=ASSET)
        clients.append(client)

    connections = api.mph_connections(assets=[ASSET])
    assert len(connections) == 3

    connections = api.mph_connections(assets=["BTC"])
    assert len(connections) == 0


@pytest.mark.usefixtures("picopayments_server")
def test_filters_handles():

    # fund server
    for i in range(3):
        address = lib.get_funding_addresses([ASSET])[ASSET]
        rawtx = api.create_send(**{
            'source': FUNDING_ADDRESS,
            'destination': address,
            'asset': ASSET,
            'quantity': 1000000,
            'regular_dust_size': 1000000
        })
        api.sendrawtransaction(tx_hex=rawtx)

    # connect clients
    assert len(api.mph_connections()) == 0
    clients = []
    for i in range(3):
        bob_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=bob_wif))
        client.connect(1000000, 65535, asset=ASSET)
        clients.append(client)
    alpha, beta, gamma = clients

    connections = api.mph_connections(handles=[alpha.handle, beta.handle])
    assert len(connections) == 2

    connections = api.mph_connections(handles=["deadbeef"])
    assert len(connections) == 0


def test_verifies_assets():
    pass  # FIXME test it


def test_verifies_handles():
    pass  # FIXME test it
