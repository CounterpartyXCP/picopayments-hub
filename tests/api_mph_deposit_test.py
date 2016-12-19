import os
import tempfile
import pytest
import jsonschema

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from picopayments_hub import lib
from picopayments_hub import api
from picopayments_hub import err
from picopayments_cli import auth
from micropayment_core import util
from micropayment_core.scripts import compile_deposit_script


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
DEPOSIT_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "deposit_script": {"type": "string"},
        "next_revoke_secret_hash": {"type": "string"},
        "signature": {"type": "string"},
        "pubkey": {"type": "string"},
    },
    "required": [
        "deposit_script", "next_revoke_secret_hash", "signature", "pubkey"
    ],
    "additionalProperties": False
}


@pytest.mark.usefixtures("picopayments_server")
def test_validate_handle_exists():
    try:
        asset = "XCP"
        client_key = lib.create_key(asset, netcode="XTN")
        next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        c2h_deposit_script = util.b2h(os.urandom(32)),
        params = {
            "handle": "deadbeef",
            "deposit_script": c2h_deposit_script,
            "next_revoke_secret_hash": next_revoke_secret_hash
        }
        params = auth.sign_json(params, client_key["wif"])
        api.mph_deposit(**params)
        assert False
    except err.HandleNotFound:
        assert True


@pytest.mark.usefixtures("picopayments_server")
def test_validate_deposit_not_already_given():
    try:
        asset = "XCP"
        client_key = lib.create_key(asset, netcode="XTN")
        client_pubkey = client_key["pubkey"]

        h2c_spend_secret = util.b2h(os.urandom(32))
        h2c_spend_secret_hash = util.hash160hex(
            h2c_spend_secret
        )

        params = {
            "asset": asset,
            "spend_secret_hash": h2c_spend_secret_hash
        }
        params = auth.sign_json(params, client_key["wif"])
        result = api.mph_request(**params)

        handle = result["handle"]
        hub_pubkey = result["pubkey"]
        c2h_spend_secret_hash = result["spend_secret_hash"]

        c2h_deposit_script = compile_deposit_script(
            client_pubkey, hub_pubkey, c2h_spend_secret_hash, 1337
        )

        # submit deposit
        next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))

        params = {
            "handle": handle,
            "deposit_script": c2h_deposit_script,
            "next_revoke_secret_hash": next_revoke_secret_hash
        }
        params = auth.sign_json(params, client_key["wif"])
        result = api.mph_deposit(**params)
        assert result is not None
        jsonschema.validate(result, DEPOSIT_RESULT_SCHEMA)

        # resubmit deposit
        next_revoke_secret_hash = util.hash160hex(util.b2h(os.urandom(32)))
        params = {
            "handle": handle,
            "deposit_script": c2h_deposit_script,
            "next_revoke_secret_hash": next_revoke_secret_hash
        }
        params = auth.sign_json(params, client_key["wif"])
        result = api.mph_deposit(**params)

        assert False
    except err.DepositAlreadyGiven:
        assert True
