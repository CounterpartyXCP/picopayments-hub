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
from micropayment_core import scripts
from tests import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


def get_txs(txids):
    return api.getrawtransaction_batch(txhash_list=txids)


@pytest.mark.usefixtures("picopayments_server")
def test_standard_usage(server_db):

    # fund server
    for i in range(4):
        address = lib.get_funding_address()
        unsigned_rawtx = api.create_send(**{
            'source': FUNDING_ADDRESS,
            'destination': address,
            'asset': ASSET,
            'quantity': 1000000,
            'regular_dust_size': 1000000
        })
        signed_rawtx = scripts.sign_deposit(
            get_txs, FUNDING_WIF, unsigned_rawtx
        )
        api.sendrawtransaction(tx_hex=signed_rawtx)

    # connect clients
    assert len(api.mph_status()["connections"]) == 0
    clients = []
    for i in range(4):
        auth_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=auth_wif))
        txid = client.connect(1000000, 42, asset=ASSET)
        assert txid is not None

        status = client.get_status()
        assert status["send_balance"] == 1000000
        assert status["send_deposit_ttl"] is not None
        assert status["recv_deposit_ttl"] is None  # hub deposit not yet made
        clients.append(client)
    assert len(api.mph_status()["connections"]) == 4

    # server funds deposits
    assert len(cron.fund_deposits()) == 4
    assert len(cron.fund_deposits()) == 0
    for client in clients:
        status = client.get_status()
        assert status["recv_deposit_ttl"] is not None  # hub deposit now made

    # before status
    alpha, beta, gamma, delta = clients
    alpha_before_status = alpha.get_status()
    beta_before_status = beta.get_status()
    gamma_before_status = gamma.get_status()

    # can send multiple payments
    alpha.micro_send(beta.handle, 5, "0000")
    alpha.micro_send(gamma.handle, 6, "0001")
    assert alpha.sync() == []
    assert beta.sync() == [{
        "payer_handle": alpha.handle,
        "amount": 5,
        "token": "0000"
    }]
    assert gamma.sync(), [{
        "payer_handle": alpha.handle,
        "amount": 6,
        "token": "0001"
    }]

    # send more back, commits are revoked to maximize liquidity
    beta.micro_send(alpha.handle, 42, "0003")
    assert beta.sync() == []
    assert alpha.sync() == [{
        "payer_handle": beta.handle,
        "amount": 42,
        "token": "0003"
    }]

    # multiple syncs/commtis from single client
    alpha.micro_send(beta.handle, 1, "0004")
    assert alpha.sync() == []

    # get after status
    alpha_after_status = alpha.get_status()
    beta_after_status = beta.get_status()
    gamma_after_status = gamma.get_status()

    # compare statuses
    alpha_after_status["send_balance"] == alpha_before_status[
        "send_balance"] + 27
    beta_after_status["send_balance"] == beta_before_status[
        "send_balance"] - 40
    gamma_after_status["send_balance"] == gamma_before_status[
        "send_balance"] + 5

    # client | c2h active | h2c active
    # -------+------------+-----------
    # alpha  | 1 commit   | 1 commit
    # beta   | 1 commit   | 0 commit
    # gamma  | 0 commit   | 1 commit
    # delta  | 0 commit   | 0 commit
    assert len(alpha.c2h_state["commits_active"]) == 1
    assert len(alpha.h2c_state["commits_active"]) == 1
    assert len(beta.c2h_state["commits_active"]) == 1
    assert len(beta.h2c_state["commits_active"]) == 0
    assert len(gamma.c2h_state["commits_active"]) == 0
    assert len(gamma.h2c_state["commits_active"]) == 1
    assert len(delta.c2h_state["commits_active"]) == 0
    assert len(delta.h2c_state["commits_active"]) == 0
