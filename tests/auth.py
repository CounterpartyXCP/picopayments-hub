import unittest
from counterpartylib.lib.micropayments import util
from picopayments import auth


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

    # TODO test errors / bad auth


if __name__ == "__main__":
    unittest.main()
