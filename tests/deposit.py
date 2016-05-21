import unittest
import picopayments


ASSET = "A14456548018133352000"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


PAYER_WIF = "cT5RVbfLsgdUv2EAmbckFXNcsj9EmdAVvU9m6aarXb3fUpt9xkjX"
PAYEE_PUBKEY = (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
)
SPEND_SECRET_HASH = "a7ec62542b0d393d43442aadf8d55f7da1e303cb"
EXPIRE_TIME = 5
QUANTITY = 1337
EXPECTED_DEPOSIT = {
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
    "script": (
        "635221033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bd"
        "e0210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
        "52ae6763a914a7ec62542b0d393d43442aadf8d55f7da1e303cb8821033faa57e0ed3a"
        "3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0ac6755b27521033faa"
        "57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb3402d0daa29d808e2bde0ac6868"
    ),
}

EXPECTED_STATE = {
    "payout_rawtxs": [],
    "payer_wif": "cT5RVbfLsgdUv2EAmbckFXNcsj9EmdAVvU9m6aarXb3fUpt9xkjX",
    "payee_wif": None,
    "commits_revoked": [],
    "commits_active": [],
    "commits_requested": [],
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

    def tearDown(self):
        self.channel.stop()

    def test_deposit(self):
        deposit_info = self.channel.deposit(
            PAYER_WIF, PAYEE_PUBKEY, SPEND_SECRET_HASH,
            EXPIRE_TIME, QUANTITY
        )
        self.assertEqual(EXPECTED_DEPOSIT, deposit_info)
        save_state = self.channel.save()
        self.assertEqual(EXPECTED_STATE, save_state)


if __name__ == "__main__":
    unittest.main()
