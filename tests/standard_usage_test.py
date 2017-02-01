import tempfile
import pytest

# this is require near the top to do setup of the test suite
# from counterpartylib.test import conftest

from counterpartylib.test.util_test import CURR_DIR as CPLIB_TESTDIR
from counterpartylib.test.fixtures.params import DP
from counterpartylib.test import util_test
from micropayment_core.keys import address_from_wif
from picopayments_cli.mph import Mph
from picopayments_hub import api
from picopayments_hub import lib
from picopayments_hub import db
from picopayments_hub import cron
from micropayment_core import scripts
from tests import util


FIXTURE_SQL_FILE = CPLIB_TESTDIR + '/fixtures/scenarios/unittest_fixture.sql'
FIXTURE_DB = tempfile.gettempdir() + '/fixtures.unittest_fixture.db'
ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


def get_tx(txid):
    return api.getrawtransaction(tx_hash=txid)


def _check_rawtxs(result, payout=0, revoke=0, change=0, expire=0, commit=0):
    return (
        len(result["payout"]) == payout and
        len(result["revoke"]) == revoke and
        len(result["change"]) == change and
        len(result["expire"]) == expire and
        len(result["commit"]) == commit
    )


def _assert_states_synced(handle, c2h_state, h2c_state):
    connection = db.hub_connection(handle=handle)
    db_h2c_state = db.load_channel_state(connection["h2c_channel_id"],
                                         connection["asset"])
    db_c2h_state = db.load_channel_state(connection["c2h_channel_id"],
                                         connection["asset"])
    assert c2h_state["asset"] == db_c2h_state["asset"]
    assert h2c_state["asset"] == db_h2c_state["asset"]
    assert c2h_state["deposit_script"] == db_c2h_state["deposit_script"]
    assert h2c_state["deposit_script"] == db_h2c_state["deposit_script"]

    c2h_scripts = [x["script"] for x in c2h_state["commits_active"]]
    db_c2h_scripts = [x["script"] for x in db_c2h_state["commits_active"]]
    assert c2h_scripts == db_c2h_scripts

    h2c_scripts = [x["script"] for x in h2c_state["commits_active"]]
    db_h2c_scripts = [x["script"] for x in db_h2c_state["commits_active"]]
    assert h2c_scripts == db_h2c_scripts


@pytest.mark.usefixtures("picopayments_server")
def test_standard_usage(server_db):

    # fund server
    for i in range(4):
        address = lib.get_funding_addresses([ASSET])[ASSET]
        unsigned_rawtx = api.create_send(**{
            'source': FUNDING_ADDRESS,
            'destination': address,
            'asset': ASSET,
            'quantity': 1000000,
            'regular_dust_size': 1000000
        })
        signed_rawtx = scripts.sign_deposit(
            get_tx, FUNDING_WIF, unsigned_rawtx
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

    # close alpha payment channel
    #        | h2c | c2h |
    # -------+-----+-----+
    # commit |  X  |  X  |
    # payout |  X  |  X  |
    # change |  X  |  X  |
    assert len(api.mph_status()["connections"]) == 4
    assert alpha.close() is not None        # H2C COMMIT TX
    assert len(api.mph_status()["connections"]) == 3
    assert _check_rawtxs(alpha.update())  # h2c payout delay not yet passed
    util_test.create_next_block(server_db)  # let payout delay pass
    assert _check_rawtxs(alpha.update(), payout=1)  # H2C PAYOUT TX

    # H2C CHANGE TX, C2H COMMIT TX
    assert _check_rawtxs(cron.run_all(), change=1, commit=1)

    util_test.create_next_block(server_db)  # let c2h payout delay pass
    assert _check_rawtxs(cron.run_all(), payout=1)  # C2H PAYOUT TX
    assert _check_rawtxs(alpha.update(), change=1)  # C2H CHANGE TX

    # close beta payment channel
    # recover | h2c | c2h |
    # --------+-----+-----+
    # commit  |  -  |  X  |
    # payout  |  -  |  X  |
    # change  |  X  |  X  |
    assert len(api.mph_status()["connections"]) == 3
    assert beta.close() is None
    assert len(api.mph_status()["connections"]) == 2
    # H2C CHANGE TX, C2H COMMIT TX
    assert _check_rawtxs(cron.run_all(), change=1, commit=1)
    util_test.create_next_block(server_db)  # let payout delay pass
    assert _check_rawtxs(cron.run_all(), payout=1)  # C2H PAYOUT TX
    assert _check_rawtxs(beta.update(), change=1)  # C2H CHANGE TX

    # close gamma payment channel
    # recover | h2c | c2h |
    # --------+-----+-----+
    # commit  |  X  |  -  |
    # payout  |  X  |  -  |
    # change  |  X  |  X  |
    assert len(api.mph_status()["connections"]) == 2
    assert gamma.close() is not None        # H2C COMMIT TX
    assert len(api.mph_status()["connections"]) == 1
    assert _check_rawtxs(gamma.update(), change=1)  # C2H CHANGE TX
    assert _check_rawtxs(gamma.update(), payout=1)  # H2C PAYOUT TX
    assert _check_rawtxs(cron.run_all(), change=1)  # H2C CHANGE TX

    # close delta payment channel
    # recover | h2c | c2h |
    # --------+-----+-----+
    # commit  |  -  |  -  |
    # payout  |  -  |  -  |
    # change  |  X  |  X  |
    assert len(api.mph_status()["connections"]) == 1
    assert delta.close() is None
    assert len(api.mph_status()["connections"]) == 0
    assert _check_rawtxs(delta.update(), change=1)  # C2H CHANGE TX
    assert _check_rawtxs(cron.run_all(), change=1)  # H2C CHANGE TX

    _assert_states_synced(alpha.handle, alpha.c2h_state, alpha.h2c_state)
    _assert_states_synced(beta.handle, beta.c2h_state, beta.h2c_state)
    _assert_states_synced(gamma.handle, gamma.c2h_state, gamma.h2c_state)
    _assert_states_synced(delta.handle, delta.c2h_state, delta.h2c_state)


@pytest.mark.usefixtures("picopayments_server")
def test_hub_doesnt_publish_commit(server_db):
    pass


@pytest.mark.usefixtures("picopayments_server")
def test_user_doesnt_publish_commit(server_db):

    # fund server
    for i in range(2):
        address = lib.get_funding_addresses([ASSET])[ASSET]
        unsigned_rawtx = api.create_send(**{
            'source': FUNDING_ADDRESS,
            'destination': address,
            'asset': ASSET,
            'quantity': 1000000,
            'regular_dust_size': 1000000
        })
        signed_rawtx = scripts.sign_deposit(get_tx, FUNDING_WIF,
                                            unsigned_rawtx)
        api.sendrawtransaction(tx_hex=signed_rawtx)

    # connect clients
    assert len(api.mph_status()["connections"]) == 0
    clients = []
    for i in range(2):
        auth_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=auth_wif))
        txid = client.connect(1000000, 42, asset=ASSET)
        assert txid is not None

        status = client.get_status()
        assert status["send_balance"] == 1000000
        assert status["send_deposit_ttl"] is not None
        assert status["recv_deposit_ttl"] is None  # hub deposit not yet made
        clients.append(client)
    assert len(api.mph_status()["connections"]) == 2

    # server funds deposits
    assert len(cron.fund_deposits()) == 2
    assert len(cron.fund_deposits()) == 0
    for client in clients:
        status = client.get_status()
        assert status["recv_deposit_ttl"] is not None  # hub deposit now made

    # before status
    alpha, beta = clients

    # send funds to beta
    alpha.micro_send(beta.handle, 42)
    alpha.sync()
    alpha_status = alpha.get_status()
    assert alpha_status["send_balance"] == 1000000 - 42 - 1

    # beta received funds
    beta.sync()
    beta_status = beta.get_status()
    assert beta_status["send_balance"] == 1000000 + 42 - 1

    # return some funds to alpha
    beta.micro_send(alpha.handle, 13)
    beta.sync()
    beta_status = beta.get_status()
    assert beta_status["send_balance"] == 1000000 + 42 - 1 - 13 - 1

    # alpha received funds
    alpha.sync()
    alpha_status = alpha.get_status()
    assert alpha_status["send_balance"] == 1000000 - 42 - 1 + 13 - 1

    # beta settles
    assert len(api.mph_status()["connections"]) == 2
    assert beta.close() is not None  # H2C COMMIT TX
    assert len(api.mph_status()["connections"]) == 1
    assert _check_rawtxs(beta.update())  # h2c payout delay not yet passed
    util_test.create_next_block(server_db)  # let payout delay pass
    assert _check_rawtxs(beta.update(), payout=1)  # H2C PAYOUT TX
    # H2C CHANGE TX, C2H COMMIT TX
    assert _check_rawtxs(cron.run_all(), change=1, commit=1)
    util_test.create_next_block(server_db)  # let c2h payout delay pass
    assert _check_rawtxs(cron.run_all(), payout=1)  # C2H PAYOUT TX
    assert _check_rawtxs(beta.update(), change=1)  # C2H CHANGE TX

    # let channel expire
    for i in range(50):
        util_test.create_next_block(server_db)

    # hub closes alice channel
    #        | h2c | c2h |
    # -------+-----+-----+
    # commit |  -  |  X  |
    # payout |  -  |  X  |
    # change |  -  |  -  |
    # expire |  X  |  -  |
    # C2H COMMIT TX, H2C EXPIRE TX
    assert _check_rawtxs(cron.run_all(), commit=1, expire=1)
    assert _check_rawtxs(cron.run_all(), payout=1)  # C2H PAYOUT TX

    # FIXME check entire h2c deposit recovered
    # FIXME assert _check_rawtxs(alpha.update(), change=1)
    # FIXME check tx transfer amounts and resulting balances
