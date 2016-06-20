# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import json
import unittest
import btctxstore
from picopayments import scripts


FIXTURES = json.load(open("tests/sign.fixtures.json"))


class TestSign(unittest.TestCase):

    def setUp(self):
        self.btctxstore = btctxstore.BtcTxStore(testnet=True, dryrun=True)

    def test_sign_deposit(self):
        rawtx = scripts.sign_deposit(
            self.btctxstore,
            **FIXTURES["deposit"]["input"])
        self.assertEqual(rawtx, FIXTURES["deposit"]["expected"])

    def test_sign_created_commit(self):
        rawtx = scripts.sign_created_commit(
            self.btctxstore, **FIXTURES["created_commit"]["input"]
        )
        self.assertEqual(rawtx, FIXTURES["created_commit"]["expected"])

    def test_sign_finalize_commit(self):
        rawtx = scripts.sign_finalize_commit(
            self.btctxstore, **FIXTURES["finalize_commit"]["input"]
        )
        self.assertEqual(rawtx, FIXTURES["finalize_commit"]["expected"])

    def test_sign_revoke_recover(self):
        rawtx = scripts.sign_revoke_recover(
            self.btctxstore, **FIXTURES["revoke_recover"]["input"]
        )
        self.assertEqual(rawtx, FIXTURES["revoke_recover"]["expected"])

    def test_sign_payout_recover(self):
        rawtx = scripts.sign_payout_recover(
            self.btctxstore, **FIXTURES["payout_recover"]["input"]
        )
        self.assertEqual(rawtx, FIXTURES["payout_recover"]["expected"])

    def test_sign_change_recover(self):
        rawtx = scripts.sign_change_recover(
            self.btctxstore, **FIXTURES["change_recover"]["input"]
        )
        self.assertEqual(rawtx, FIXTURES["change_recover"]["expected"])

    def test_sign_expire_recover(self):
        rawtx = scripts.sign_expire_recover(
            self.btctxstore, **FIXTURES["expire_recover"]["input"]
        )
        self.assertEqual(rawtx, FIXTURES["expire_recover"]["expected"])


if __name__ == "__main__":
    unittest.main()
