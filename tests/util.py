import copy
from picopayments_hub import api
from picopayments_hub import etc
from picopayments_cli import auth
from micropayment_core.keys import generate_wif
from micropayment_core.keys import address_from_wif
from counterpartylib.test.fixtures.params import DP
from micropayment_core import scripts


def get_txs(txids):
    return api.getrawtransaction_batch(txhash_list=txids)


class MockAPI(object):

    def __init__(self, url="http://127.0.0.1:15000/api/", auth_wif=None,
                 username=None, password=None, verify_ssl_cert=False):
        self.url = url
        self.auth_wif = auth_wif
        self.username = username
        self.password = password
        self.verify_ssl_cert = verify_ssl_cert

    def __getattribute__(self, name):
        props = ["url", "auth_wif", "username", "password", "verify_ssl_cert"]
        auth_methods = ["mph_request", "mph_deposit", "mph_sync", "mph_close"]
        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(*args, **kwargs):
            kwargs = copy.deepcopy(kwargs)  # simulate http serialization
            if name in auth_methods:
                kwargs = auth.sign_json(kwargs, self.auth_wif)
            result = object.__getattribute__(api, name)(**kwargs)
            if name in auth_methods:
                auth.verify_json(result)
            return result
        return wrapper


def gen_funded_wif(asset, asset_quantity, btc_quantity):
    src_wif = DP["addresses"][0][2]
    src_address = address_from_wif(src_wif)
    dest_wif = generate_wif(netcode=etc.netcode)
    dest_address = address_from_wif(dest_wif)
    unsigned_rawtx = api.create_send(**{
        'source': src_address,
        'destination': dest_address,
        'asset': asset,
        'quantity': asset_quantity,
        'regular_dust_size': btc_quantity
    })
    signed_rawtx = scripts.sign_deposit(get_txs, src_wif, unsigned_rawtx)
    api.sendrawtransaction(tx_hex=signed_rawtx)
    return dest_wif
