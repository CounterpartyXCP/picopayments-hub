import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test.fixtures.params import DP
from micropayment_core.keys import address_from_wif
from picopayments_cli.mph import Mph
from picopayments_hub import api
from picopayments_hub import lib
from picopayments_hub import cron
from tests import util


# from tests.util import MockAPI


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


@pytest.mark.usefixtures("picopayments_server")
def test_simulation_xcp():

    # fund server
    for i in range(2):
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
    clients = []
    for i in range(2):
        bob_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=bob_wif))
        txid = client.connect(1000000, 65535, asset=ASSET)
        assert txid is not None

        status = client.get_status()
        assert status["send_balance"] == 1000000
        assert status["send_deposit_ttl"] is not None
        assert status["recv_deposit_ttl"] is None  # hub deposit not yet made

        clients.append(client)

    # server funds deposits
    cron.run_all()
    for client in clients:
        status = client.get_status()
        assert status["recv_deposit_ttl"] is not None  # hub deposit now made

    # FIXME implement simulation test
