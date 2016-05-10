import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


OPEN_STATE = {
    "payer_wif": "cRFw92LUdNwkyy6uvNb4yLatySiCiiEN1gscQnf8iZYhYLZG9Ro1",
    "deposit_rawtx": (
        "010000000184763c748fd7b7f10a7755ebec390cac90ac30b19f74a874f192b379"
        "a99f8c74000000006b4830450221009c730b454dff76fbb0c130c32cd13f6b0a46"
        "52371289e5f5e7b54135134a074602203a2699819b9f3c17a2ebfc69b0a6fa29f0"
        "23e37680eb58d9c52f4f741354ecc8012103f71179e931904043eb4cc9b1b0d7df"
        "1a2c27f68812eced8e53b98ee004cf36c1ffffffff03d2b400000000000017a914"
        "3e4fe6f243858e350785442381431f95909720b78700000000000000001e6a1cc5"
        "c5e5796db8055af5f366696617c2f1fc35c0b3de44913a374e2f4c5e3102000000"
        "00001976a9145cc53459271a9cc509f00f769f2634005ba5243288ac00000000",
    ),
    "payee_pubkey": (
        "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
    ),
    "timeout_rawtx": None,
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


class TestRecover(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.channel.stop()

    def test_haggle(self):
        pass  # TODO implement and test


if __name__ == "__main__":
    unittest.main()
