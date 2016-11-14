import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test.fixtures.params import DP
from counterpartylib.test import util_test
from micropayment_core.keys import address_from_wif
from picopayments_client.mph import Mph
from picopayments import api
from picopayments import lib
from picopayments import cron
from tests import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


@pytest.mark.usefixtures("picopayments_server")
def test_standard_usage(server_db):

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
    clients = []
    for i in range(3):
        bob_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=bob_wif))
        txid = client.connect(1000000, 65535, asset=ASSET)
        assert txid is not None

        status = client.get_status()
        assert status["balance"] == 1000000
        assert status["c2h_deposit_ttl"] is not None
        assert status["h2c_deposit_ttl"] is None  # hub deposit not yet made
        clients.append(client)

    # server funds deposits
    assert len(cron.fund_deposits()) == 3
    assert len(cron.fund_deposits()) == 0
    for client in clients:
        status = client.get_status()
        assert status["h2c_deposit_ttl"] is not None  # hub deposit now made

    # after before status
    alpha, beta, gamma = clients
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

    # get after status
    alpha_after_status = alpha.get_status()
    beta_after_status = beta.get_status()
    gamma_after_status = gamma.get_status()

    # compare statuses
    alpha_after_status["balance"] == alpha_before_status["balance"] + 29
    beta_after_status["balance"] == beta_before_status["balance"] - 39
    gamma_after_status["balance"] == gamma_before_status["balance"] + 5

    assert alpha.close() is not None  # commit txid returned (block created)
    assert len(alpha.update()) == 0  # payout delay not yet passed
    util_test.create_next_block(server_db)  # create block and let delay pass
    assert len(alpha.update()) == 1  # payout txid

    assert beta.close() is not None  # commit txid returned (block created)
    assert len(beta.update()) == 0  # payout delay not yet passed
    util_test.create_next_block(server_db)  # create block and let delay pass
    assert len(beta.update()) == 1  # payout txid

    assert gamma.close() is not None  # commit txid returned (block created)
    assert len(gamma.update()) == 0  # payout delay not yet passed
    util_test.create_next_block(server_db)  # create block and let delay pass
    assert len(gamma.update()) == 1  # payout txid

    # hub close connections cron
    cron.run_all()

    # recover c2h change
    assert len(alpha.update()) == 1  # txid
    assert len(beta.update()) == 1  # txid
    assert len(gamma.update()) == 1  # txid
