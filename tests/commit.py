import json
import unittest
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


FIXTURES = json.load(open("tests/fixtures.json"))


PAYER_BEFORE = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "payer_wif": "cSthi1Ye1sbHepC5s8rNukQBAKLCyct6hLg6MCH9Ybk1cKfGcPb2",
    "deposit_script": (
        "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5"
        "2103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae"
        "6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a5"
        "51f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443"
        "bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868"),
    "commits_active": [],
    "payee_wif": None,
    "commits_revoked": [],
    "spend_secret": None,
    "commits_requested": []}


PAYEE_BEFORE_REQUEST = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "payer_wif": None,
    "deposit_script": (
        "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5"
        "2103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae"
        "6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a5"
        "51f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443"
        "bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868"
    ),
    "commits_active": [],
    "payee_wif": "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc",
    "commits_revoked": [],
    "spend_secret": (
        "d688fc3400f9feb6f8c409b804c75deaa5fa1635bf252d5d5de262a5c63cb5e5"
    ),
    "commits_requested": []
}


PAYER_AFTER = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "commits_active": [
        {
            "rawtx": "01000000017231934b8873769b325c090a99dd7e5a3d8708bf13e94f677228b90787631f0700000000fd460100483045022100ea61f098fdaf5b26f7b37b578ac0dcde84aec1169aa45f84a876ff97075e29c602205ec1abeb2be0efb3891e4b1cc88cc687ab8dd3c0cf7f04202b6ff1be2fe523fd01483045022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036414002207fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a001514cb063522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868ffffffff03463c00000000000017a914b57a70f9301cfd13603fc36b3162b57340b3958b8700000000000000001e6a1c5144cf3299cdb4115af7e5b1a21ecac52fedaf164910f4fe4beb0a877c5100000000000017a9145c6f176aa8bab82688c8b07562595a622d7b889a8700000000",
            "script": "6355b275a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a8611ac67a914bcc82b07e3c1317a52d7adbff1ef869d4e46ac35882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac68",
            "revoke_secret": None
        }
    ],
    "spend_secret": None,
    "payee_wif": None,
    "payer_wif": "cSthi1Ye1sbHepC5s8rNukQBAKLCyct6hLg6MCH9Ybk1cKfGcPb2",
    "deposit_script": "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868",
    "commits_requested": [],
    "commits_revoked": []
}


REVOKE_SECRET_HASH = "bcc82b07e3c1317a52d7adbff1ef869d4e46ac35"


PAYEE_AFTER_REQUEST = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "commits_requested": [
        "b9724d0ef63b346e77ba0316978beae6af63d823f0ebc1c8199e22d52a4274b0"
    ],
    "commits_active": [],
    "deposit_script": (
        "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5"
        "2103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae"
        "6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a5"
        "51f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443"
        "bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868"
    ),
    "commits_revoked": [],
    "spend_secret": (
        "d688fc3400f9feb6f8c409b804c75deaa5fa1635bf252d5d5de262a5c63cb5e5"
    ),
    "payer_wif": None,
    "payee_wif": "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc",
}


PAYEE_AFTER_SET_COMMIT = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "commits_active": [
        {
            "rawtx": "01000000017231934b8873769b325c090a99dd7e5a3d8708bf13e94f677228b90787631f0700000000fd460100483045022100ea61f098fdaf5b26f7b37b578ac0dcde84aec1169aa45f84a876ff97075e29c602205ec1abeb2be0efb3891e4b1cc88cc687ab8dd3c0cf7f04202b6ff1be2fe523fd01483045022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036414002207fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a001514cb063522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868ffffffff03463c00000000000017a914b57a70f9301cfd13603fc36b3162b57340b3958b8700000000000000001e6a1c5144cf3299cdb4115af7e5b1a21ecac52fedaf164910f4fe4beb0a877c5100000000000017a9145c6f176aa8bab82688c8b07562595a622d7b889a8700000000",
            "script": "6355b275a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a8611ac67a914bcc82b07e3c1317a52d7adbff1ef869d4e46ac35882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac68",
            "revoke_secret": "b9724d0ef63b346e77ba0316978beae6af63d823f0ebc1c8199e22d52a4274b0"
        }
    ],
    "deposit_script": "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868",
    "commits_revoked": [],
    "spend_secret": "d688fc3400f9feb6f8c409b804c75deaa5fa1635bf252d5d5de262a5c63cb5e5",
    "payee_wif": "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc",
    "payer_wif": None,
    "commits_requested": []
}


SET_COMMIT = {
    "script": "6355b275a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a8611ac67a914bcc82b07e3c1317a52d7adbff1ef869d4e46ac35882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac68",
    "rawtx": "01000000017231934b8873769b325c090a99dd7e5a3d8708bf13e94f677228b90787631f0700000000fd460100483045022100ea61f098fdaf5b26f7b37b578ac0dcde84aec1169aa45f84a876ff97075e29c602205ec1abeb2be0efb3891e4b1cc88cc687ab8dd3c0cf7f04202b6ff1be2fe523fd01483045022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036414002207fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a001514cb063522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868ffffffff03463c00000000000017a914b57a70f9301cfd13603fc36b3162b57340b3958b8700000000000000001e6a1c5144cf3299cdb4115af7e5b1a21ecac52fedaf164910f4fe4beb0a877c5100000000000017a9145c6f176aa8bab82688c8b07562595a622d7b889a8700000000"
}


DELAY_TIME = 5


PAYEE_BEFORE_CLOSE = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "payee_wif": "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc",
    "commits_active": [
        {
            "revoke_secret": "8050c5b75cfec7f7c76fcfffe0b90cde3f0e37e404a540386ff58dcee3fbf4c2",
            "rawtx": "01000000017231934b8873769b325c090a99dd7e5a3d8708bf13e94f677228b90787631f0700000000fd460100483045022100fe849b43cc4bede5c1af9515f9e79ded1776d3163331727cd592d89a78e308da0220026fb2e681d8c7e721159f35d4e6708981e751d9c573cd7221077837d613a66601483045022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036414002207fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a001514cb063522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868ffffffff03463c00000000000017a91454eda5ac68f27ba781f559307be015d12fdec8018700000000000000001e6a1c5144cf3299cdb4115af7e5b1a21ecac52fedaf164910f4fe4beb0a837c5100000000000017a9145c6f176aa8bab82688c8b07562595a622d7b889a8700000000",
            "script": "6355b275a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a8611ac67a914f9e38472e9430f864151f3013350497bf86fe4b0882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac68"
        }
    ],
    "payer_wif": None,
    "spend_secret": "d688fc3400f9feb6f8c409b804c75deaa5fa1635bf252d5d5de262a5c63cb5e5",
    "deposit_script": "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868",
    "commits_requested": [],
    "commits_revoked": []
}


PAYEE_AFTER_CLOSE = {
    "payout_rawtxs": [],
    "revoke_rawtxs": [],
    "spend_secret": "d688fc3400f9feb6f8c409b804c75deaa5fa1635bf252d5d5de262a5c63cb5e5",
    "deposit_script": "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868",
    "payee_wif": "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc",
    "commits_requested": [],
    "commits_revoked": [],
    "commits_active": [
        {
            "script": "6355b275a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a8611ac67a914f9e38472e9430f864151f3013350497bf86fe4b0882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac68",
            "revoke_secret": "8050c5b75cfec7f7c76fcfffe0b90cde3f0e37e404a540386ff58dcee3fbf4c2",
            "rawtx": "01000000017231934b8873769b325c090a99dd7e5a3d8708bf13e94f677228b90787631f0700000000fd460100483045022100fe849b43cc4bede5c1af9515f9e79ded1776d3163331727cd592d89a78e308da0220026fb2e681d8c7e721159f35d4e6708981e751d9c573cd7221077837d613a66601483045022100eea344bec9052b271040c69ad6d8a9fce2a860f26e8ff75ddaa361fb399df4c202200df793c7b938301f283802f8d42425709a4d45d1afdf43fa1135e9a2a94505be01514cb063522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868ffffffff03463c00000000000017a91454eda5ac68f27ba781f559307be015d12fdec8018700000000000000001e6a1c5144cf3299cdb4115af7e5b1a21ecac52fedaf164910f4fe4beb0a837c5100000000000017a9145c6f176aa8bab82688c8b07562595a622d7b889a8700000000"
        }
    ],
    "payer_wif": None
}


CLOSE_TXID = "cae4f025dedbaba4bb470b1e46ffcd916d8ffce597019950b25b7307b531843d"


CLOSE_TOPUBLISH = {
    "rawtx": "01000000017231934b8873769b325c090a99dd7e5a3d8708bf13e94f677228b90787631f0700000000fd460100483045022100fe849b43cc4bede5c1af9515f9e79ded1776d3163331727cd592d89a78e308da0220026fb2e681d8c7e721159f35d4e6708981e751d9c573cd7221077837d613a66601483045022100eea344bec9052b271040c69ad6d8a9fce2a860f26e8ff75ddaa361fb399df4c202200df793c7b938301f283802f8d42425709a4d45d1afdf43fa1135e9a2a94505be01514cb063522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868ffffffff03463c00000000000017a91454eda5ac68f27ba781f559307be015d12fdec8018700000000000000001e6a1c5144cf3299cdb4115af7e5b1a21ecac52fedaf164910f4fe4beb0a837c5100000000000017a9145c6f176aa8bab82688c8b07562595a622d7b889a8700000000",
    "script": "63522102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d52103c7b09d53bdb0ef9cfea06c1e6f2192e6a91cdeac209402bc36c1c368021a861152ae6763a9144cc776751eb4d41f23feaf94697cb7ec2fe597a4882102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6703ffff00b2752102a73443bc32f5fec6a551f71af75311b0876686156d16d367562d3d29987792d5ac6868"
}


class TestCommit(unittest.TestCase):

    def setUp(self):
        self.payer = picopayments.Channel(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.payee = picopayments.Channel(
            ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
        )
        self.maxDiff = None

    def test_request_commit(self):
        result = self.payee.request_commit(PAYEE_BEFORE_REQUEST, 1)
        hash_bin = picopayments.util.h2b(result["revoke_secret_hash"])
        self.assertEqual(len(hash_bin), 20)
        self.assertEqual(result["quantity"], 1)

    def test_create_commit(self):
        result = self.payer.create_commit(PAYER_BEFORE, 1,
                                          REVOKE_SECRET_HASH, DELAY_TIME)
        self.assertEqual(
            result, FIXTURES["test_commit"]["create_commit_result"]
        )
        self.assertEqual(result["channel_state"], PAYER_AFTER)

    def test_set_commit(self):
        result = self.payee.set_commit(
            PAYEE_AFTER_REQUEST,
            SET_COMMIT["rawtx"],
            SET_COMMIT["script"]
        )
        self.assertEqual(result["channel_state"], PAYEE_AFTER_SET_COMMIT)

    def test_funds_flow(self):
        payer_state = PAYER_BEFORE
        payee_state = PAYEE_BEFORE_REQUEST

        # send funds
        for quantity in range(1, 10):

            result = self.payee.request_commit(payee_state, quantity)
            payee_state = result["channel_state"]

            result = self.payer.create_commit(payer_state, result["quantity"],
                                              result["revoke_secret_hash"],
                                              DELAY_TIME)
            payer_state = result["channel_state"]
            rawtx = result["tosign"]["rawtx"]
            commit_script = result["commit_script"]

            result = self.payee.set_commit(payee_state, rawtx, commit_script)
            payee_state = result["channel_state"]

        self.assertEqual(self.payer.get_transferred_amount(payer_state), 9)
        self.assertEqual(self.payee.get_transferred_amount(payee_state), 9)

        # reverse funds
        result = self.payee.revoke_until(payee_state, 4)
        payee_state = result["channel_state"]

        result = self.payer.revoke_all(payer_state, result["revoke_secrets"])
        payer_state = result["channel_state"]

        self.assertEqual(self.payer.get_transferred_amount(payer_state), 4)
        self.assertEqual(self.payee.get_transferred_amount(payee_state), 4)

    def test_publish(self):
        result = self.payee.close_channel(PAYEE_BEFORE_CLOSE)
        self.assertEqual(result["topublish"], CLOSE_TOPUBLISH)
        self.assertEqual(PAYEE_AFTER_CLOSE, result["channel_state"])


if __name__ == "__main__":
    unittest.main()
