# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
import requests
from requests.auth import HTTPBasicAuth
from picopayments import auth
from picopayments import err
from picopayments import cfg


def call(url, method, params, username=None, password=None,
         verify_ssl_cert=True, authentication_wif=None):

    if authentication_wif:
        params = auth.sign_json(params, authentication_wif)

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

    result = response["result"]
    if authentication_wif:
        auth.verify_json(result)

    return result


def counterparty_call(method, params):
    return call(
        cfg.counterparty_url, method, params,
        username=cfg.counterparty_username,
        password=cfg.counterparty_password
    )
