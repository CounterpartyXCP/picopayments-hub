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


FIXTURES = json.load(open("tests/fixtures.json"))


class TestRevoke(unittest.TestCase):

    def setUp(self):
        self.payer = picopayments.Channel(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.maxDiff = None

    def tearDown(self):
        self.payer.stop()

    def test_revoke(self):
        self.payer.load(FIXTURES["test_revoke"]["state_before"])
        self.payer.payer_update()
        # print(json.dumps(self.payer.save(), indent=2))
        self.assertEqual(
            self.payer.save(), FIXTURES["test_revoke"]["state_after"]
        )


if __name__ == "__main__":
    unittest.main()
