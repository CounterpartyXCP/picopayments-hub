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
PAYER_CLOSED = FIXTURES["test_payout"]["payer_closed"]
PAYEE_CLOSED = FIXTURES["test_payout"]["payee_closed"]
PAYEE_AFTER = FIXTURES["test_payout"]["payee_after"]


# print('"payer_closed":', json.dumps(PAYER_CLOSED, indent=2))
# print('"payee_closed":', json.dumps(PAYEE_CLOSED, indent=2))
# print('"payee_after":', json.dumps(PAYEE_AFTER, indent=2))


class TestPayout(unittest.TestCase):

    def setUp(self):
        self.payee = picopayments.channel.Payee(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.payee.stop()

    def test_get_payout_recoverable(self):
        self.payee.load(PAYEE_CLOSED)
        scripts = self.payee.get_payout_recoverable()
        self.assertTrue(len(scripts) > 0)

    def test_payout_recover(self):
        self.payee.load(PAYEE_CLOSED)
        self.payee.update()
        self.assertEqual(self.payee.save(), PAYEE_AFTER)


if __name__ == "__main__":
    unittest.main()
