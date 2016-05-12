import unittest
import picopayments


ASSET = "A14456548018133352000"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


ALPHA_PAYER_WIF = "cT5RVbfLsgdUv2EAmbckFXNcsj9EmdAVvU9m6aarXb3fUpt9xkjX"
ALPHA_PAYEE_PUBKEY = (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
)
ALPHA_SPEND_SECRET_HASH = "a7ec62542b0d393d43442aadf8d55f7da1e303cb"
ALPHA_EXPIRE_TIME = 5
ALPHA_QUANTITY = 1337
ALPHA_EXPECTED_INFO = {
  "asset": "A14456548018133352000",
  "rawtx": (
    "0100000001dab5588f6df29b3f3b650f57b443bb2dbd9ba8d113dbf1f80b18b60f1a71"
    "0447000000006b483045022100ba5366aa8f8110ae52bc6ed3916ca1fcf86e7c11d621"
    "9dc398ecda528a0e4c6c02205f7e4b6177ff6a8f526fcb7ce946a70dbb0d356ca29eeb"
    "a665e90fd2a2a2889c0121033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb340"
    "2d0daa29d808e2bde0ffffffff03d2b400000000000017a914aa6d4750bb4db850b48e"
    "e784c5ad275f235b7f768700000000000000001e6a1cd9a71f04d5096e06527153002f"
    "7a950091739ca38e74120a36361f565e310200000000001976a914e960d8c0c0d4ee53"
    "6912b4e115fb8b8d84d5330b88ac00000000"
  ),
  "quantity": 1337,
  "txid": "9a602185541095aac7e59b7d6942a800aef6358e0dee5004a9cdfb085a9908a5",
  "script": (
    "635221033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bd"
    "e0210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
    "52ae6763a914a7ec62542b0d393d43442aadf8d55f7da1e303cb8821033faa57e0ed3a"
    "3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0ac6755b27521033faa"
    "57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0ac6868"
  ),
  "address": "2N8nMmhmPoxTXckZV2h9HvcNedmjB65LzBz"
}

ALPHA_EXPECTED_STATE = {
  "payee_pubkey": (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
  ),
  "payer_wif": "cT5RVbfLsgdUv2EAmbckFXNcsj9EmdAVvU9m6aarXb3fUpt9xkjX",
  "payee_wif": None,
  "payer_pubkey": (
    "033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0"
  ),
  "timeout_rawtx": None,
  "deposit_script_hex": (
    "635221033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bd"
    "e0210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
    "52ae6763a914a7ec62542b0d393d43442aadf8d55f7da1e303cb8821033faa57e0ed3a"
    "3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0ac6755b27521033faa"
    "57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0ac6868"
  ),
  "spend_secret": None,
  "change_rawtx": None,
  "deposit_rawtx": (
    "0100000001dab5588f6df29b3f3b650f57b443bb2dbd9ba8d113dbf1f80b18b60f1a71"
    "0447000000006b483045022100ba5366aa8f8110ae52bc6ed3916ca1fcf86e7c11d621"
    "9dc398ecda528a0e4c6c02205f7e4b6177ff6a8f526fcb7ce946a70dbb0d356ca29eeb"
    "a665e90fd2a2a2889c0121033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb340"
    "2d0daa29d808e2bde0ffffffff03d2b400000000000017a914aa6d4750bb4db850b48e"
    "e784c5ad275f235b7f768700000000000000001e6a1cd9a71f04d5096e06527153002f"
    "7a950091739ca38e74120a36361f565e310200000000001976a914e960d8c0c0d4ee53"
    "6912b4e115fb8b8d84d5330b88ac00000000"
  )
}


class TestDeposit(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.maxDiff = None

    def tearDown(self):
        self.channel.stop()

    def test_deposit(self):
        deposit_info = self.channel.deposit(
            ALPHA_PAYER_WIF, ALPHA_PAYEE_PUBKEY, ALPHA_SPEND_SECRET_HASH,
            ALPHA_EXPIRE_TIME, ALPHA_QUANTITY
        )
        self.assertEqual(ALPHA_EXPECTED_INFO, deposit_info)
        save_state = self.channel.save()
        self.assertEqual(ALPHA_EXPECTED_STATE, save_state)

    def test_depositing_to_open(self):
        pass


if __name__ == "__main__":
    unittest.main()
