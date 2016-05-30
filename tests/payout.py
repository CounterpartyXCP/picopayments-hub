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
PAYEE_CLOSED = FIXTURES["test_payout"]["payee_closed"]
PAYEE_AFTER = FIXTURES["test_payout"]["payee_after"]


class TestPayout(unittest.TestCase):

    def setUp(self):
        self.payee = picopayments.Channel(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.payee.stop()

    def test_payout_recover(self):
        self.payee.load(PAYEE_CLOSED)
        self.payee.payee_update()
        self.assertEqual(self.payee.save(), PAYEE_AFTER)


if __name__ == "__main__":
    unittest.main()
