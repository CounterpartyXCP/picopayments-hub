import unittest
import pyelliptic
from counterpartylib.lib.micropayments import util
from picopayments import auth


class TestAuth(unittest.TestCase):

    def test_sign_verify(self):
        data = b"f483"

        wif = util.random_wif()
        signature = auth.sign(wif, data)

        pubkey = util.wif2pubkey(wif)
        result = auth.verify(pubkey, signature, data)

        self.assertTrue(result)

    def test_sign_verify_json(self):
        json_data = {"wif": util.random_wif(), "foo": "bar"}
        signed_json_data = auth.sign_json(json_data)
        self.assertNotIn("wif", signed_json_data)
        result = auth.verify_json(signed_json_data)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
