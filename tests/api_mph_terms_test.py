import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from picopayments import api
from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


@pytest.mark.usefixtures("picopayments_server")
def test_standard_usage_xcp():
    # TODO test input validation

    # test gets all
    terms = api.mph_terms()
    assert(terms == {
        "BTC": {
            "deposit_max": 0,
            "deposit_min": 0,
            "deposit_ratio": 1.0,
            "expire_max": 0,
            "expire_min": 0,
            "sync_fee": 1
        },
        "XCP": {
            "deposit_max": 0,
            "deposit_min": 0,
            "deposit_ratio": 1.0,
            "expire_max": 0,
            "expire_min": 0,
            "sync_fee": 1
        },
        "A7736697071037023001": {
            "deposit_max": 0,
            "deposit_min": 0,
            "deposit_ratio": 1.0,
            "expire_max": 0,
            "expire_min": 0,
            "sync_fee": 1
        }
    })

    # test limits to asset
    terms = api.mph_terms(assets=["XCP"])
    assert(terms == {
        "XCP": {
            "deposit_max": 0,
            "deposit_min": 0,
            "deposit_ratio": 1.0,
            "expire_max": 0,
            "expire_min": 0,
            "sync_fee": 1
        },
    })
