# import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


PAYER_BEFORE = {
  "payer_wif": "cRFw92LUdNwkyy6uvNb4yLatySiCiiEN1gscQnf8iZYhYLZG9Ro1",
  "change_rawtx": None,
  "payee_wif": None,
  "revoked_commits": [],
  "active_commits": [],
  "deposit_script_hex": (
      "63522103f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e53b98ee004"
      "cf36c12103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368"
      "021a861152ae6763a914f8320aeb45ed0fa07447b6a1e4ff3a7e6cd4dfee882103"
      "f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e53b98ee004cf36c1ac"
      "6703ffff00b2752103f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e"
      "53b98ee004cf36c1ac6868"
  ),
  "timeout_rawtx": None,
  "spend_secret": None,
  "deposit_rawtx": (
      "01000000010b081ef30aa3de2a2c79079cc584e781dda8c292b76e9879b66b6944"
      "ee1efe7a020000006a47304402207949937be48aef0df098522532d238541cdab7"
      "5b61e34a7e2098d178faaa5be3022044e2ecf85fa9ebd08ca60b11bd15979373ed"
      "b77eb5368237e18f700e3fe93414012103f71179e931904043eb4cc9b1b0d7df1a"
      "2c27f68812eced8e53b98ee004cf36c1ffffffff03d2b400000000000017a914a8"
      "785b3899415ad153dadf14e1375744130058268700000000000000001e6a1c18fd"
      "cc0a3b365a715a44ba45edc93aa5d06a02c53820de74079b0fd47c550100000000"
      "001976a9145cc53459271a9cc509f00f769f2634005ba5243288ac00000000"
  )
}


PAYEE_BEFORE = {
  "payer_wif": None,
  "change_rawtx": None,
  "payee_wif": "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc",
  "revoked_commits": [],
  "active_commits": [],
  "deposit_script_hex": (
      "63522103f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e53b98ee004"
      "cf36c12103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368"
      "021a861152ae6763a914f8320aeb45ed0fa07447b6a1e4ff3a7e6cd4dfee882103"
      "f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e53b98ee004cf36c1ac"
      "6703ffff00b2752103f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e"
      "53b98ee004cf36c1ac6868"
  ),
  "timeout_rawtx": None,
  "spend_secret": (
      "ca572d8a58e8403a22c9e6653206fab2cf060171f5f13fe458a5a997dc0a8101"
  ),
  "deposit_rawtx": (
      "01000000010b081ef30aa3de2a2c79079cc584e781dda8c292b76e9879b66b6944"
      "ee1efe7a020000006a47304402207949937be48aef0df098522532d238541cdab7"
      "5b61e34a7e2098d178faaa5be3022044e2ecf85fa9ebd08ca60b11bd15979373ed"
      "b77eb5368237e18f700e3fe93414012103f71179e931904043eb4cc9b1b0d7df1a"
      "2c27f68812eced8e53b98ee004cf36c1ffffffff03d2b400000000000017a914a8"
      "785b3899415ad153dadf14e1375744130058268700000000000000001e6a1c18fd"
      "cc0a3b365a715a44ba45edc93aa5d06a02c53820de74079b0fd47c550100000000"
      "001976a9145cc53459271a9cc509f00f769f2634005ba5243288ac00000000"
  )
}


class TestCommit(unittest.TestCase):

    def setUp(self):
        self.payer = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.payee = picopayments.channel.Payee(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.payer.stop()
        self.payee.stop()

    def test_commit(self):
        self.payee.load(PAYEE_BEFORE)
        self.payer.load(PAYER_BEFORE)

        # self.payee.


if __name__ == "__main__":
    unittest.main()
