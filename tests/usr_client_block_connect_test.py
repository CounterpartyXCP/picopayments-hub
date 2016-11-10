import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments_client import mph
from tests import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_standard_usage():
    bob_wif = util.gen_funded_wif("XCP", 1000000, 1000000)
    client = mph.Mph(util.MockAPI(auth_wif=bob_wif))
    txid = client.connect(1337, 65535, asset="XCP", dryrun=True)
    assert txid is not None
