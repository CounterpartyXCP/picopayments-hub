# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
import requests
from requests.auth import HTTPBasicAuth
from picopayments import auth
from picopayments import err
from picopayments import etc


CALL_LOCAL_PROCESS = False


def _http_call(url, method, params={}, username=None,
               password=None, verify_ssl_cert=True):
    payload = {"method": method, "params": params, "jsonrpc": "2.0", "id": 0}
    kwargs = {
        "url": url,
        "headers": {'content-type': 'application/json'},
        "data": json.dumps(payload),
        "verify": verify_ssl_cert,
    }
    if username and password:
        kwargs["auth"] = HTTPBasicAuth(username, password)
    response = requests.post(**kwargs).json()
    if "result" not in response:
        raise err.RpcCallFailed(payload, response)
    return response["result"]


def call(url, method, params={}, username=None, password=None,
         verify_ssl_cert=True, auth_wif=None):

    if auth_wif:
        params = auth.sign_json(params, auth_wif)

    if CALL_LOCAL_PROCESS:
        from picopayments import api
        result = getattr(api, method)(**params)
    else:
        result = _http_call(
            url, method, params=params, username=username,
            password=password, verify_ssl_cert=verify_ssl_cert
        )  # pragma: no cover
    if auth_wif:
        auth.verify_json(result)

    return result


def cp_call(method, params={}):
    return _http_call(
        etc.counterparty_url, method, params=params,
        username=etc.counterparty_username,
        password=etc.counterparty_password
    )


class RPC(object):

    def __init__(self, url, auth_wif=None, username=None,
                 password=None, verify_ssl_cert=True):
        self.url = url
        self.auth_wif = auth_wif
        self.username = username
        self.password = password
        self.verify_ssl_cert = verify_ssl_cert

    def __getattribute__(self, name):
        props = ["url", "auth_wif", "username", "password", "verify_ssl_cert"]
        auth_methods = ["mpc_hub_request", "mpc_hub_deposit", "mpc_hub_sync"]

        if name in props:
            return object.__getattribute__(self, name)

        def wrapper(**kwargs):
            return call(
                url=self.url, method=name, params=kwargs,
                auth_wif=self.auth_wif if name in auth_methods else None,
                verify_ssl_cert=self.verify_ssl_cert,
                username=self.username, password=self.password,
            )
        return wrapper
