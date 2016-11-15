from counterpartylib.test.conftest import *  # NOQA


import os
import shutil
import tempfile
from picopayments import srv
from picopayments import api
from picopayments import lib
from picopayments import cron
from picopayments_client.mph import Mph
from micropayment_core.util import gettxid
from micropayment_core.keys import address_from_wif
from counterpartylib.lib import config
from counterpartylib.test import util_test
from counterpartylib.test.fixtures.params import DP
from tests import util


ASSET = "XCP"
FUNDING_WIF = DP["addresses"][0][2]  # XTC: 91950000000, BTC: 199909140
FUNDING_ADDRESS = address_from_wif(FUNDING_WIF)


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
        util_test.insert_raw_transaction(tx_hex, server_db)
        return gettxid(tx_hex)
    api.sendrawtransaction = sendrawtransaction

    def tear_down():
        shutil.rmtree(tempdir)

    request.addfinalizer(tear_down)


@pytest.fixture(scope="function")
def connected_clients():

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

    # FIMXE fund seconde asset

    # connect clients
    clients = []
    for i in range(3):
        bob_wif = util.gen_funded_wif(ASSET, 1000000, 1000000)
        client = Mph(util.MockAPI(auth_wif=bob_wif))
        client.connect(1000000, 42, asset=ASSET)
        clients.append(client)
    cron.fund_deposits()

    # FIMXE connect clients to second asset

    return clients
