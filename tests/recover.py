import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


EXPIRED_STATE = {
    "payer_wif": "cMtErY7rdk8gycybQ9nPVQ4FchyvsMYMyQHjdgobnFMFfMU6eFj3",
    "spend_secret_hash": "a7ec62542b0d393d43442aadf8d55f7da1e303cb",
    "deposit_rawtx": (
        "010000000103fb314b25de6a000de0b9227a1fbf1439d355fb5f1b5bfd1d1e057f"
        "9cc10413000000006a47304402203320ac3ce8017c8eb7a2881916af7eea96d0b2"
        "3915e3514669fae1f6bf115545022051a26bb842846229ac1db41d6bae0b30a5ce"
        "310731c34b4888a92ab5fdb5078c01210389bdba52b9820a4d672bbb14b6c01aa5"
        "4963cc0f1419b14a01e9ebeb62ebef1fffffffff03d2b400000000000017a914c0"
        "cb8bde9f461a63d8dddf0074a73019394bf27b8700000000000000001e6a1c8381"
        "8bbd060c6e6e029e6ab0228938cd3e4225a49bc3a832b0c60fd85e310200000000"
        "001976a9147f6ac1ca784f65f161d20b6dca3fa0b26449b58588ac00000000"
    ),
    "payee_pubkey": (
        "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
    ),
    "state": "DEPOSITING",
    "recover_rawtx": None,
    "payer_pubkey": (
        "0389bdba52b9820a4d672bbb14b6c01aa54963cc0f1419b14a01e9ebeb62ebef1f"
    ),
    "payee_wif": None,
    "spend_secret": None,
    "deposit_script_text": (
        "OP_IF OP_2 0389bdba52b9820a4d672bbb14b6c01aa54963cc0f1419b14a01e9e"
        "beb62ebef1f 0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb8"
        "2f62490f75f8 OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 a7ec62"
        "542b0d393d43442aadf8d55f7da1e303cb OP_EQUALVERIFY 0389bdba52b9820a"
        "4d672bbb14b6c01aa54963cc0f1419b14a01e9ebeb62ebef1f OP_CHECKSIG OP_"
        "ELSE OP_5 OP_NOP3 OP_DROP 0389bdba52b9820a4d672bbb14b6c01aa54963cc"
        "0f1419b14a01e9ebeb62ebef1f OP_CHECKSIG OP_ENDIF OP_ENDIF"
    )
}


class TestRecover(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.channel.stop()

    def test_recover(self):
        self.channel.load(EXPIRED_STATE)
        new_state = self.channel.update()
        self.assertEqual(new_state, "RECOVERING")


if __name__ == "__main__":
    unittest.main()
