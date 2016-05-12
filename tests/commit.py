import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


OPEN_STATE_ALPHA = {
    "payer_wif": "cRFw92LUdNwkyy6uvNb4yLatySiCiiEN1gscQnf8iZYhYLZG9Ro1",
    "deposit_rawtx": (
        "010000000184763c748fd7b7f10a7755ebec390cac90ac30b19f74a874f192b379"
        "a99f8c74000000006b4830450221009c730b454dff76fbb0c130c32cd13f6b0a46"
        "52371289e5f5e7b54135134a074602203a2699819b9f3c17a2ebfc69b0a6fa29f0"
        "23e37680eb58d9c52f4f741354ecc8012103f71179e931904043eb4cc9b1b0d7df"
        "1a2c27f68812eced8e53b98ee004cf36c1ffffffff03d2b400000000000017a914"
        "3e4fe6f243858e350785442381431f95909720b78700000000000000001e6a1cc5"
        "c5e5796db8055af5f366696617c2f1fc35c0b3de44913a374e2f4c5e3102000000"
        "00001976a9145cc53459271a9cc509f00f769f2634005ba5243288ac00000000"
    ),
    "payee_pubkey": (
        "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
    ),
    "timeout_rawtx": None,
    "chaneg_rawtx": None,
    "payer_pubkey": (
        "03f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e53b98ee004cf36c1"
    ),
    "payee_wif": None,
    "spend_secret": None,
    "deposit_script_text": (
        "OP_IF OP_2 03f71179e931904043eb4cc9b1b0d7df1a2c27f68812eced8e53b98"
        "ee004cf36c1 0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb8"
        "2f62490f75f8 OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 a7ec62"
        "542b0d393d43442aadf8d55f7da1e303cb OP_EQUALVERIFY 03f71179e9319040"
        "43eb4cc9b1b0d7df1a2c27f68812eced8e53b98ee004cf36c1 OP_CHECKSIG OP_"
        "ELSE OP_5 OP_NOP3 OP_DROP 03f71179e931904043eb4cc9b1b0d7df1a2c27f6"
        "8812eced8e53b98ee004cf36c1 OP_CHECKSIG OP_ENDIF OP_ENDIF",
    )
}

OPEN_STATE_BETA = {
  "timeout_rawtx": None,
  "deposit_script_text": (
    "OP_IF OP_2 [02dcf5cf02849bb046d2ef38630051ed1806e33d1183e3419ce9440c1e"
    "40fd8df1] [0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f624"
    "90f75f8] OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 [c1fc72735bfea"
    "c8686cbc9e81195d7241c00e813] OP_EQUALVERIFY [02dcf5cf02849bb046d2ef386"
    "30051ed1806e33d1183e3419ce9440c1e40fd8df1] OP_CHECKSIG OP_ELSE [000001"
    "] OP_NOP3 OP_DROP [02dcf5cf02849bb046d2ef38630051ed1806e33d1183e3419ce"
    "9440c1e40fd8df1] OP_CHECKSIG OP_ENDIF OP_ENDIF"
  ),
  "payee_wif": None,
  "deposit_rawtx": (
    "01000000017e3eca0eb622ea6bd70948fed674490de7709b11f9232eb5750bca599ff7"
    "f4f1000000006b4830450221009f869d1cfbc6fb9040324b8681396f04501b13a6cf9b"
    "e34f999167dcf439c3ff02205122349fa7e9e157112437d344011602a464e6aa0ee8a0"
    "09cd68f14fe7893f2b012102dcf5cf02849bb046d2ef38630051ed1806e33d1183e341"
    "9ce9440c1e40fd8df1ffffffff03d2b400000000000017a9148b406cb97d4b38d20ca4"
    "a1cd08b12a03e2fdb3d98700000000000000001e6a1cbab937184a4e3a2aecc2c8200f"
    "485d2b885a20dd46768b84b4de59d55e310200000000001976a914e79a70d3c7c8367b"
    "d98593f7413d6186be8968d988ac00000000"
  ),
  "change_rawtx": None,
  "spend_secret": None,
  "payer_pubkey": (
    "02dcf5cf02849bb046d2ef38630051ed1806e33d1183e3419ce9440c1e40fd8df1"
  ),
  "payer_wif": (
    "cUZoCj8cmBJBzuRFsBbyjRU2cjC2e9eu2B4KnGo1buxxZ8LKQYWq"
  ),
  "payee_pubkey": (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
  )
}

OPEN_STATE_GAMMA = {
  "payee_pubkey": (
      "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
  ),
  "deposit_rawtx": (
    "0100000001aa2092b8ad2cf4838d6ff490d059c7f05eb2f256646dc5b66d3164978915"
    "a1f8000000006a47304402200bc59a9785075c185b4f3e8a4c3cbbeb9fefd9f95fd401"
    "287e18c2254b91296702207cfd37d40d1e3ee6a288ff6cbd42d280cc08fe2be3ae1ea0"
    "74a13f638988acfa01210207629868d8919b284b0ab65d239b8d33d8c0b6b4871d0790"
    "7e606c0b99e5049cffffffff03d2b400000000000017a914ada475afdefaef30f3d16e"
    "2d706aeece3580b6058700000000000000001e6a1c282669ef0c29b3d090d27f71aa9c"
    "585e0936608ec62783c8303285c15e310200000000001976a9146aee7761ad0f251af6"
    "cc664de7e20f67f072ee3888ac00000000"
  ),
  "spend_secret": None,
  "payee_wif": None,
  "deposit_script_text": (
    "OP_IF OP_2 [0207629868d8919b284b0ab65d239b8d33d8c0b6b4871d07907e606c0b"
    "99e5049c] [0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f624"
    "90f75f8] OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 [c1fc72735bfea"
    "c8686cbc9e81195d7241c00e813] OP_EQUALVERIFY [0207629868d8919b284b0ab65"
    "d239b8d33d8c0b6b4871d07907e606c0b99e5049c] OP_CHECKSIG OP_ELSE [000001"
    "] OP_NOP3 OP_DROP [0207629868d8919b284b0ab65d239b8d33d8c0b6b4871d07907"
    "e606c0b99e5049c] OP_CHECKSIG OP_ENDIF OP_ENDIF"
  ),
  "payer_pubkey": (
      "0207629868d8919b284b0ab65d239b8d33d8c0b6b4871d07907e606c0b99e5049c"
  ),
  "payer_wif": "cQrWnTcmDaqM32PTgx8zfBaxv2CUoLJxbn3JMvo6XNJg8jobXRXP",
  "change_rawtx": None,
  "timeout_rawtx": None
}


class TestCommit(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.channel.stop()

    def test_commit(self):
        pass  # TODO implement and test


if __name__ == "__main__":
    unittest.main()
