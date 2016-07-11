# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import json
import requests
from requests.auth import HTTPBasicAuth


class Api(object):

    def __init__(self, user, password, url, testnet):
        self.url = url
        self.user = user
        self.password = password

    def call(self, method, params):
        payload = {
            "method": method, "params": params, "jsonrpc": "2.0", "id": 0
        }
        headers = {'content-type': 'application/json'}
        auth = HTTPBasicAuth(self.user, self.password)
        response = requests.post(self.url, data=json.dumps(payload),
                                 headers=headers, auth=auth)
        response_data = json.loads(response.text)
        if "result" not in response_data:
            print(json.dumps(payload, indent=2))
            raise Exception("Rpc call failed! {0}".format(
                repr(response.text)
            ))
        return response_data["result"]
