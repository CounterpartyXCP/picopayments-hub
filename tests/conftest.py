from counterpartylib.test.conftest import *  # NOQA


import os
import shutil
import tempfile
from picopayments import srv
from picopayments import api
from micropayment_core.util import gettxid
from counterpartylib.lib import config
from counterpartylib.test import util_test


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
