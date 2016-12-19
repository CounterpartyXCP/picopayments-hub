import os
import jsonschema
import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments_hub import lib
from picopayments_hub import api
from picopayments_hub import err
from picopayments_cli import auth
from micropayment_core import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'


REQUEST_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "channel_terms": {"type": "object"},  # TODO validate terms format
        "pubkey": {"type": "string"},
        "signature": {"type": "string"},
        "spend_secret_hash": {"type": "string"},
        "handle": {"type": "string"},
    },
    "required": [
        "signature", "channel_terms", "pubkey", "spend_secret_hash", "handle"
    ],
    "additionalProperties": False
}


@pytest.mark.usefixtures("picopayments_server")
def test_standard_usage_xcp():
    asset = "XCP"
    client_key = lib.create_key(asset)
    secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
    params = {
        "asset": asset,
        "spend_secret_hash": secret_hash,
        "hub_rpc_url": "https://does.not.exist",
    }
    params = auth.sign_json(params, client_key["wif"])
    result = api.mph_request(**params)
    assert result is not None
    jsonschema.validate(result, REQUEST_RESULT_SCHEMA)


@pytest.mark.usefixtures("picopayments_server")
def test_validate_asset_in_terms():
    try:
        asset = "DIVISIBLE"
        client_key = lib.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {"asset": asset, "spend_secret_hash": secret_hash}
        params = auth.sign_json(params, client_key["wif"])
        api.mph_request(**params)
        assert False
    except err.AssetNotInTerms:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_validate_asset_exists():
    try:
        asset = "NONEXISTINGASSET"
        client_key = lib.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {"asset": asset, "spend_secret_hash": secret_hash}
        params = auth.sign_json(params, client_key["wif"])
        api.mph_request(**params)
        assert False
    except err.AssetDoesNotExist:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_validate_url():
    try:
        asset = "XCP"
        client_key = lib.create_key(asset)
        secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {
            "asset": asset,
            "spend_secret_hash": secret_hash,
            "hub_rpc_url": "?? invalid url ??",
        }
        params = auth.sign_json(params, client_key["wif"])
        api.mph_request(**params)
        assert False
    except err.InvalidUrl:
        assert True
