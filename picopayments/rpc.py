# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
import requests
from requests.auth import HTTPBasicAuth
from . import config
from . import auth
from . import exceptions


def call(url, method, params, username=None, password=None,
         verify=True, jsonauth=False):

    if jsonauth:
        params = auth.sign_json(params)

    payload = {"method": method, "params": params, "jsonrpc": "2.0", "id": 0}

    kwargs = {
        "url": url,
        "headers": {'content-type': 'application/json'},
        "data": json.dumps(payload),
        "verify": verify,
    }
    if username and password:
        kwargs["auth"] = HTTPBasicAuth(username, password)
    response = requests.post(**kwargs).json()
    if "result" not in response:
        raise exceptions.RpcCallFailed(payload, response)

    result = response["result"]
    if jsonauth:
        auth.verify_json(result)

    return result


def counterparty_call(method, params):
    return call(
        config.counterparty_url, method, params,
        username=config.counterparty_username,
        password=config.counterparty_password
    )
