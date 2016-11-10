import copy
from picopayments import api
from picopayments_client import auth
from micropayment_core import keys
from micropayment_core.keys import generate_wif
from micropayment_core.keys import address_from_wif
from counterpartylib.test.fixtures.params import DP


class MockAPI(object):

    def __init__(self, url=None, auth_wif=None, username=None,
                 password=None, verify_ssl_cert=True):
        self.url = "http://127.0.0.1:15000/api/"
        self.auth_wif = auth_wif
        self.username = username
        self.password = password
        self.verify_ssl_cert = False

    def __getattribute__(self, name):
        props = ["url", "auth_wif", "username", "password", "verify_ssl_cert"]
        auth_methods = ["mph_request", "mph_deposit", "mph_sync"]
        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(*args, **kwargs):
            kwargs = copy.deepcopy(kwargs)  # simulate http serialization
            if name in auth_methods:
                privkey = keys.wif_to_privkey(self.auth_wif)
                kwargs = auth.sign_json(kwargs, privkey)
            result = object.__getattribute__(api, name)(**kwargs)
            if name in auth_methods:
                auth.verify_json(result)
            return result
        return wrapper


def gen_funded_wif(asset, asset_quantity, btc_quantity):
    src_wif = DP["addresses"][0][2]
    src_address = address_from_wif(src_wif)
    dest_wif = generate_wif(netcode="XTN")
    dest_address = address_from_wif(dest_wif)
    rawtx = api.create_send(**{
        'source': src_address,
        'destination': dest_address,
        'asset': asset,
        'quantity': asset_quantity,
        'regular_dust_size': btc_quantity
    })
    api.sendrawtransaction(tx_hex=rawtx)
    return dest_wif
