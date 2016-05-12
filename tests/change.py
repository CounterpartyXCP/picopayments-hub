import json
import unittest
import picopayments
from picopayments import util


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


PAYER_WIF = "cNEC8Ftb6g8gmpthaSJd1bqFP811FFhykF4SK1jdByPJbxzbLGGw"
SPEND_SECRET = (
    "89a4a2395b242fcf77c766fc47dc6c14399c06a197f2322c8c503da87e76d842"
)
SPEND_SECRET_HASH = util.b2h(util.hash160(util.h2b(SPEND_SECRET)))
EXPIRE_TIME = 2**16 - 1  # max
QUANTITY = 1337
PAYEE_PUBKEY = (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
)


class TestChange(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.channel.stop()

    def test_change(self):
        self.channel.deposit(
            PAYER_WIF, PAYEE_PUBKEY, SPEND_SECRET_HASH, EXPIRE_TIME, QUANTITY
        )
        # print(json.dumps(self.channel.save(), indent=2))

#   def test_change(self):
#       self.channel.load(BEFORE_STATE)
#       self.assertFalse(self.channel.can_change_recover())
#       self.channel.spend_secret = SPEND_SECRET
#       self.assertTrue(self.channel.can_change_recover())
#       self.channel.update()
#       print(json.dumps(self.channel.save(), indent=2))


if __name__ == "__main__":
    unittest.main()
