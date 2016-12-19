import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from picopayments_hub import etc
from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments_cli.mpc import Mpc
from tests import util
from micropayment_core import keys


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_block_send():
    alice_wif = util.gen_funded_wif("XCP", 1000000, 1000000)
    client = Mpc(util.MockAPI(auth_wif=alice_wif))
    bob_wif = keys.generate_wif(netcode=etc.netcode)
    bob_address = keys.address_from_wif(bob_wif)
    txid = client.block_send(source=alice_wif, destination=bob_address,
                             asset="XCP", quantity=42)
    assert txid is not None
