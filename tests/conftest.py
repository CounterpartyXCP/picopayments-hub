from counterpartylib.test.conftest import *  # NOQA


import os
import shutil
import tempfile
from jsonrpc import dispatcher
from picopayments_hub import srv
from picopayments_hub import api
from picopayments_hub import lib
from picopayments_hub import cron
from picopayments_cli.mph import Mph
from micropayment_core.keys import address_from_wif
from counterpartylib.lib import config
from counterpartylib.test import util_test
from counterpartylib.test.fixtures.params import DP
from counterpartylib.lib.micropayments import validate
from tests import util
from micropayment_core import scripts


FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


def get_txs(txids):
    return api.getrawtransaction_batch(txhash_list=txids)


@pytest.fixture(scope="function")
def picopayments_server(request, server_db):

    # setup
    tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
    basedir = os.path.join(tempdir, "basedir")
    shutil.copytree("tests/fixtures", basedir)

    srv.main([
        "--testnet",
        "--basedir={0}".format(basedir),
        "--cp_url={0}".format(config.RPC),
        "--cp_username={0}".format(config.RPC_USER),
        "--cp_password={0}".format(config.RPC_PASSWORD)
    ], serve=False)

    # monkeypatch sendrawtransaction to send tx and create new block
    def sendrawtransaction(tx_hex):
        validate.tx_signature(dispatcher, tx_hex)
        result = util_test.insert_raw_transaction(tx_hex, server_db)
        return result["tx_hash"]
    api.sendrawtransaction = sendrawtransaction

    def tear_down():
        shutil.rmtree(tempdir)

    request.addfinalizer(tear_down)


@pytest.fixture(scope="function")
def connected_clients():

    # create asset
    unsigned_rawtx = api.create_issuance(
        source=FUNDING_ADDRESS,
        asset="A7736697071037023001",
        quantity=100000000
    )
    signed_rawtx = scripts.sign_deposit(
        get_txs, FUNDING_WIF, unsigned_rawtx
    )
    api.sendrawtransaction(tx_hex=signed_rawtx)

    # fund server
    for i in range(3):
        address = lib.get_funding_address()
        for asset in ["XCP", "A7736697071037023001"]:
            unsigned_rawtx = api.create_send(**{
                'source': FUNDING_ADDRESS,
                'destination': address,
                'asset': asset,
                'quantity': 1000000,
                'regular_dust_size': 1000000
            })
            signed_rawtx = scripts.sign_deposit(
                get_txs, FUNDING_WIF, unsigned_rawtx
            )
            api.sendrawtransaction(tx_hex=signed_rawtx)

    # connect clients
    clients = []

    # fund XCP clients
    for i in range(3):
        wif = util.gen_funded_wif("XCP", 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=wif))
        client.connect(1000000, expire_time=42, asset="XCP")
        clients.append(client)

    # fund A7736697071037023001 clients
    for i in range(3):
        wif = util.gen_funded_wif("A7736697071037023001", 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=wif))
        client.connect(1000000, expire_time=42, asset="A7736697071037023001")
        clients.append(client)

    cron.fund_deposits()

    return clients
