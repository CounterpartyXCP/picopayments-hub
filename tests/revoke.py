# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/revoke.fixtures.json"))


class TestRevoke(unittest.TestCase):

    def setUp(self):
        self.api = picopayments.Api(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def test_revoke(self):
        payer_state = FIXTURES["payer_state"]
        result = self.api.payer_recoverables(payer_state)
        self.assertEqual(result, FIXTURES["update_result"])


if __name__ == "__main__":
    unittest.main()
