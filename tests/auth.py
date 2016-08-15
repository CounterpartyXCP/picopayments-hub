import unittest
from counterpartylib.lib.micropayments import util
from picopayments import auth
from picopayments import err


class TestAuth(unittest.TestCase):

    def test_sign_verify(self):
        data = b"f483"

        wif = util.random_wif()
        signature = auth.sign(wif, data)

        pubkey = util.wif2pubkey(wif)
        auth.verify(pubkey, signature, data)

    def test_sign_verify_json(self):
        signed_json_data = auth.sign_json({"foo": "bar"}, util.random_wif())
        auth.verify_json(signed_json_data)

    def test_auth_pubkey_missmatch(self):

        def func():
            data = {"foo": "bar", "pubkey": "invalid"}
            signed_json_data = auth.sign_json(data, util.random_wif())
            auth.verify_json(signed_json_data)

        self.assertRaises(err.AuthPubkeyMissmatch, func)

    def test_invalid_signature(self):

        def func():
            signature = auth.sign(util.random_wif(), b"foo")
            pubkey = util.wif2pubkey(util.random_wif())
            auth.verify(pubkey, signature, b"bar")

        self.assertRaises(err.InvalidSignature, func)


if __name__ == "__main__":
    unittest.main()
