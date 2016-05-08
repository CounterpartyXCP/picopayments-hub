import unittest
import picopayments


ASSET = "A14456548018133352000"
WIF = "cUHmoq4jPpdjxFQWh9iEtuehtYjeMpSQe8Sz4rkxoBwjTKoCn4m5"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


class TestControl(unittest.TestCase):

    def setUp(self):
        self.control = picopayments.control.Control(
            ASSET, user=USER, password=PASSWORD,
            api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN,
        )

    def test_balance(self):
        address = self.control.btctxstore.get_address(WIF)
        asset_balance, btc_balance = self.control.get_balance(address)
        self.assertEqual(asset_balance, 1337)
        self.assertEqual(btc_balance, 61720)


if __name__ == "__main__":
    unittest.main()
