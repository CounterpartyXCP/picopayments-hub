import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


EXPIRED_STATE = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "payer_wif": "cMtErY7rdk8gycybQ9nPVQ4FchyvsMYMyQHjdgobnFMFfMU6eFj3",
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
    "commits_revoked": [],
    "commits_active": [],
    "commits_requested": [],
    "change_rawtx": None,
    "expire_rawtx": None,
    "payee_wif": None,
    "spend_secret": None,
    "deposit_script_hex": (
        "6352210389bdba52b9820a4d672bbb14b6c01aa54963cc0f1419b14a01e9ebeb62ebef"
        "1f210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
        "52ae6763a914a7ec62542b0d393d43442aadf8d55f7da1e303cb88210389bdba52b982"
        "0a4d672bbb14b6c01aa54963cc0f1419b14a01e9ebeb62ebef1fac6755b275210389bd"
        "ba52b9820a4d672bbb14b6c01aa54963cc0f1419b14a01e9ebeb62ebef1fac6868"
    )
}


RECOVERING_STATE = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "deposit_script_hex": (
        "6352210399e3dde1d1853dbd99c81ba4f2c0cca351b3cceecce7cd0bd59acc57896721"
        "35210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
        "52ae6763a914a7ec62542b0d393d43442aadf8d55f7da1e303cb88210399e3dde1d185"
        "3dbd99c81ba4f2c0cca351b3cceecce7cd0bd59acc5789672135ac6755b275210399e3"
        "dde1d1853dbd99c81ba4f2c0cca351b3cceecce7cd0bd59acc5789672135ac6868"
    ),
    "commits_revoked": [],
    "commits_active": [],
    "commits_requested": [],
    "change_rawtx": None,
    "payee_wif": None,
    "spend_secret": None,
    "deposit_rawtx": (
        "0100000001d1400bfe207056319b9c90a8526255b2b7755e19f10034811cb8b0a2"
        "02bf008b000000006a47304402204c4316848dd8dd3823bef339d1e86993350cb8"
        "98110824d96516e29ac24fb87602203e179a936093423173edde8eb0ba7aa5691b"
        "574d63642b3cf65903913d51553101210399e3dde1d1853dbd99c81ba4f2c0cca3"
        "51b3cceecce7cd0bd59acc5789672135ffffffff03d2b400000000000017a91469"
        "249459340955eab4183ffe74cb6778e8284b898700000000000000001e6a1c4b24"
        "257191d2cbb31f9b056d79191f04fad8aab4676f8a87de13bf2e5e310200000000"
        "001976a914d36d5a91d3f05b2c23cf4fdcac88e4f8b50cec9088ac00000000"
    ),
    "expire_rawtx": (
        "0200000001f4db00105cdc7cab7d26ae018154540faa2a20872a1e263c6948c5a4"
        "e44d060f00000000f947304402204c7cbcc610ac5ee744dc7de6fc31421217dbd0"
        "66e41fd377dbe16dbd70372d3d02201e74b66967b44548c007a011d98bb42a9f22"
        "651392232b87a640dcf8ad55e1d20100004cad6352210399e3dde1d1853dbd99c8"
        "1ba4f2c0cca351b3cceecce7cd0bd59acc5789672135210327f017c35a46b75953"
        "6309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f852ae6763a914a7ec6254"
        "2b0d393d43442aadf8d55f7da1e303cb88210399e3dde1d1853dbd99c81ba4f2c0"
        "cca351b3cceecce7cd0bd59acc5789672135ac6755b275210399e3dde1d1853dbd"
        "99c81ba4f2c0cca351b3cceecce7cd0bd59acc5789672135ac68680500000002c2"
        "8d0000000000001976a914d36d5a91d3f05b2c23cf4fdcac88e4f8b50cec9088ac"
        "00000000000000001e6a1cdbb957b39547c4b841700768d623a3f4c849743272bc"
        "7783855c9c4d00000000"
    ),
    "payer_wif": "cMwtNdKijb7ej6yrmkhQyfvVQ5LibNFURQ8zdpiRFWxhFJ2aohwR",
}


class TestRecover(unittest.TestCase):

    def setUp(self):
        self.channel = picopayments.channel.Payer(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )

    def tearDown(self):
        self.channel.stop()

    def test_expired_to_recovering(self):
        self.channel.load(EXPIRED_STATE)
        self.assertFalse(self.channel.is_closing())
        self.channel.update()  # publish expire tx
        self.assertTrue(self.channel.is_closing())

    def test_recovering_to_closed(self):
        self.channel.load(RECOVERING_STATE)
        self.assertTrue(self.channel.is_closed())


if __name__ == "__main__":
    unittest.main()
