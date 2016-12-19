import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments_cli.mph import Mph
from tests import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_serialization():
    auth_wif = util.gen_funded_wif("XCP", 1000000, 1000000)

    hub_api = util.MockAPI(auth_wif=auth_wif)
    client_alpha = Mph(hub_api)
    serialized_alpha = client_alpha.serialize()

    client_beta = Mph.deserialize(api=hub_api, data=serialized_alpha)
    serialized_beta = client_beta.serialize()

    assert serialized_alpha == serialized_beta
