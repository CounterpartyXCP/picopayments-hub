import unittest
import picopayments


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
SPEND_SECRET_HASH = picopayments.util.hash160hex(SPEND_SECRET)
QUANTITY = 1337
PAYEE_PUBKEY = (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
)


BEFORE_STATE = {
  "timeout_rawtx": None,
  "payer_wif": "cNEC8Ftb6g8gmpthaSJd1bqFP811FFhykF4SK1jdByPJbxzbLGGw",
  "deposit_rawtx": (
      "0100000001ea7d3ea588bd8f2bedd28e3b34c9e1d2e9e07abbf36401a0a789df10"
      "f7a101d7000000006b483045022100e4ec3f3e75f35ee1afb581c52b19feb14794"
      "f5292db353b21950fa93bdae79b102207e415a567988adbc45559f3c7e3016add4"
      "85c2e517ffab40d1f6035f9b5eed310121022eda5e6902b0978073d2fd1df6d635"
      "5f77c667df598c09621e3da926cf2af25bffffffff03d2b400000000000017a914"
      "437b283790b586fe73d93dafe697432859d752968700000000000000001e6a1cf4"
      "7dc3956e8722204e32517c4a4bf9d9d66a70e3446a4dd83c6db95c5e3102000000"
      "00001976a914c888703eb573ed80b0a5e95fafc412e7f8a152f288ac00000000"
  ),
  "spend_secret": None,
  "change_rawtx": None,
  "commits_revoked": [],
  "commits_active": [],
  "commits_requested": [],
  "deposit_script_hex": (
      "635221022eda5e6902b0978073d2fd1df6d6355f77c667df598c09621e3da926cf"
      "2af25b210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62"
      "490f75f852ae6763a914c1fc72735bfeac8686cbc9e81195d7241c00e813882102"
      "2eda5e6902b0978073d2fd1df6d6355f77c667df598c09621e3da926cf2af25bac"
      "6703ffff00b27521022eda5e6902b0978073d2fd1df6d6355f77c667df598c0962"
      "1e3da926cf2af25bac6868"
  ),
  "payee_wif": None
}


AFTER_STATE = {
  "deposit_rawtx": (
      "0100000001ea7d3ea588bd8f2bedd28e3b34c9e1d2e9e07abbf36401a0a789df10"
      "f7a101d7000000006b483045022100e4ec3f3e75f35ee1afb581c52b19feb14794"
      "f5292db353b21950fa93bdae79b102207e415a567988adbc45559f3c7e3016add4"
      "85c2e517ffab40d1f6035f9b5eed310121022eda5e6902b0978073d2fd1df6d635"
      "5f77c667df598c09621e3da926cf2af25bffffffff03d2b400000000000017a914"
      "437b283790b586fe73d93dafe697432859d752968700000000000000001e6a1cf4"
      "7dc3956e8722204e32517c4a4bf9d9d66a70e3446a4dd83c6db95c5e3102000000"
      "00001976a914c888703eb573ed80b0a5e95fafc412e7f8a152f288ac00000000"
  ),
  "commits_revoked": [],
  "commits_active": [],
  "commits_requested": [],
  "payee_wif": None,
  "payer_wif": "cNEC8Ftb6g8gmpthaSJd1bqFP811FFhykF4SK1jdByPJbxzbLGGw",
  "timeout_rawtx": None,
  "change_rawtx": (
      "0100000001e374909b18054bbfce2373428722318beab3ba45dab2bf62d33a23c7"
      "73adcc2300000000fd1d014730440220497303cb2d360db06a3dc93ce833e2c365"
      "07f9521ec0368c12cc945a4007adc7022000eb1d95a966c8ed994c9198e2c0e876"
      "98e96bb67b626949cc3e6fccec103b70012089a4a2395b242fcf77c766fc47dc6c"
      "14399c06a197f2322c8c503da87e76d84251004cb0635221022eda5e6902b09780"
      "73d2fd1df6d6355f77c667df598c09621e3da926cf2af25b210327f017c35a46b7"
      "59536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f852ae6763a914c1fc"
      "72735bfeac8686cbc9e81195d7241c00e8138821022eda5e6902b0978073d2fd1d"
      "f6d6355f77c667df598c09621e3da926cf2af25bac6703ffff00b27521022eda5e"
      "6902b0978073d2fd1df6d6355f77c667df598c09621e3da926cf2af25bac6868ff"
      "ffffff02c28d0000000000001976a914c888703eb573ed80b0a5e95fafc412e7f8"
      "a152f288ac00000000000000001e6a1c7def40b7c872501f498d8b80275098def3"
      "cd35e51a6e60d4c6eabc0700000000"
  ),
  "deposit_script_hex": (
      "635221022eda5e6902b0978073d2fd1df6d6355f77c667df598c09621e3da926cf"
      "2af25b210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62"
      "490f75f852ae6763a914c1fc72735bfeac8686cbc9e81195d7241c00e813882102"
      "2eda5e6902b0978073d2fd1df6d6355f77c667df598c09621e3da926cf2af25bac"
      "6703ffff00b27521022eda5e6902b0978073d2fd1df6d6355f77c667df598c0962"
      "1e3da926cf2af25bac6868"
  ),
  "spend_secret": (
      "89a4a2395b242fcf77c766fc47dc6c14399c06a197f2322c8c503da87e76d842"
  )
}


class TestRecoverChange(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.channel.stop()

    def test_recover_change(self):
        self.channel.load(BEFORE_STATE)
        self.assertFalse(self.channel.can_change_recover())
        self.channel.set_spend_secret(SPEND_SECRET)
        self.assertTrue(self.channel.can_change_recover())
        self.channel.update()
        self.assertEqual(self.channel.save(), AFTER_STATE)

    # TODO test for published but unconfirmed deposit


if __name__ == "__main__":
    unittest.main()
