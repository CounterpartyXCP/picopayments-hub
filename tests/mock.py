from picopayments import api
from picopayments_client import auth


class MockAPI(object):

    def __init__(self, url=None, auth_wif=None, username=None,
                 password=None, verify_ssl_cert=True):
        self.url = url
        self.auth_wif = auth_wif
        self.username = username
        self.password = password
        self.verify_ssl_cert = verify_ssl_cert

    def __getattribute__(self, name):
        props = ["url", "auth_wif", "username", "password", "verify_ssl_cert"]
        auth_methods = ["mph_request", "mph_deposit", "mph_sync"]
        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(*args, **kwargs):
            if name in auth_methods:
                kwargs = auth.sign_json(kwargs, self.auth_wif)
            result = object.__getattribute__(api, name)(**kwargs)
            if name in auth_methods:
                auth.verify_json(result)
            return result
        return wrapper
