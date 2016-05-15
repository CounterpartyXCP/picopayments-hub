import unittest
import picopayments


ASSET = "A14456548018133352000"
WIF = "cUHmoq4jPpdjxFQWh9iEtuehtYjeMpSQe8Sz4rkxoBwjTKoCn4m5"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


RAWTX = (
    "0100000001dab5588f6df29b3f3b650f57b443bb2dbd9ba8d113dbf1f80b18b60f1a71"
    "0447000000006b483045022100ba5366aa8f8110ae52bc6ed3916ca1fcf86e7c11d621"
    "9dc398ecda528a0e4c6c02205f7e4b6177ff6a8f526fcb7ce946a70dbb0d356ca29eeb"
    "a665e90fd2a2a2889c0121033faa57e0ed3a3bf89340a0a3074ce0ef403ebfb77cb340"
    "2d0daa29d808e2bde0ffffffff03d2b400000000000017a914aa6d4750bb4db850b48e"
    "e784c5ad275f235b7f768700000000000000001e6a1cd9a71f04d5096e06527153002f"
    "7a950091739ca38e74120a36361f565e310200000000001976a914e960d8c0c0d4ee53"
    "6912b4e115fb8b8d84d5330b88ac00000000"
)


class TestControl(unittest.TestCase):

    def setUp(self):
        self.control = picopayments.control.Control(
            ASSET, user=USER, password=PASSWORD,
            api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN,
        )

    def test_get_balance_alpha(self):
        address = self.control.btctxstore.get_address(WIF)
        asset_balance, btc_balance = self.control.get_balance(address)
        self.assertEqual(asset_balance, 1337)
        self.assertEqual(btc_balance, 61720)

    def test_get_balance_beta(self):
        address = "2N1fyEhjTHqdN1PNfDVpkn1CNh3gWPC7Dq2"
        asset_balance, btc_balance = self.control.get_balance(address)
        self.assertEqual(asset_balance, 1337)
        self.assertEqual(btc_balance, 46290)

    def test_get_quantity(self):
        quantity = self.control.get_quantity(RAWTX)
        self.assertEqual(quantity, 1337)
        # TODO test with confirm


if __name__ == "__main__":
    unittest.main()
