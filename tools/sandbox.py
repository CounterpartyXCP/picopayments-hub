import os
import json
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments import sql
from picopayments import db
from picopayments import lib
from picopayments import etc
from picopayments_client import util
from picopayments_client import rpc
from picopayments_client import usr
# from tests.mock import MockAPI


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestSandbox(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ], serve=False)
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @unittest.skip("it")
    def test_get_assets(self):
        url = "https://127.0.0.1:15000/api/"
        api = rpc.API(url=url, verify_ssl_cert=False)
        print(json.dumps(api.mph_terms(), indent=2))

    @unittest.skip("it")
    def test_balances(self):
        url = "https://139.59.214.74:15000/api/"
        api = rpc.API(url=url, verify_ssl_cert=False)
        client = usr.MpcClient(api)
        wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
        address = util.wif2address(wif)
        print(json.dumps(client.get_balances(address), indent=2))

    @unittest.skip("it")
    def test_balance(self):
        # url = "https://139.59.214.74:15000/api/"
        url = "https://127.0.0.1:15000/api/"
        client = usr.MpcClient(rpc.API(url=url, verify_ssl_cert=False))
        # client = usr.MpcClient(MockAPI(verify_ssl_cert=False))
        wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
        address = util.wif2address(wif)
        print(json.dumps(client.get_balances(address), indent=2))

    @unittest.skip("it")
    def test_fund(self):
        funding_wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
        asset = "A14456548018133352000"
        # asset = "XCP"
        wif = util.random_wif(netcode=etc.netcode)
        address = util.wif2address(wif)

        txid = self.client.block_send(
            source=funding_wif, destination=address,
            asset=asset, quantity=256,
            regular_dust_size=200000  # extra btc
        )

        # print("ASSET:", asset)
        # print("WIF:", wif)
        print("TXID:", txid)

    @unittest.skip("it")
    def test_burn(self):
        pass
        # wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
        # address = util.wif2address(wif)
        # unsigned_rawtx = rpc.cplib.create_burn(source=address,
        #                                        quantity=100000000)
        # txid = self.client.sign_and_publish(unsigned_rawtx, wif)
        # print("TXID:", txid)

    @unittest.skip("it")
    def test_create_expired_deposit(self):
        asset = ""
        auth_wif = ""
        client = usr.HubClient(auth_wif=auth_wif, verify_ssl_cert=False)
        deposit_txid = client.connect(42, expire_time=1,
                                      asset=asset, dryrun=True)
        self.assertIsNotNone(deposit_txid)
        print(deposit_txid)
        print(json.dumps(client.serialize(), indent=2))

    @unittest.skip("it")
    def test_show_connections(self):
        with etc.database_lock:
            cursor = sql.get_cursor()
            for hub_connection in db.hub_connections_complete():
                handle = hub_connection["handle"]
                data = lib.load_connection_data(handle, cursor)
                print("handle:", handle)
                print("hub deposit:", data["h2c_deposit_amount"])
                print("client deposit:", data["c2h_deposit_amount"])


if __name__ == "__main__":
    unittest.main()
