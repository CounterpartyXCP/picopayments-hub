import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
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
