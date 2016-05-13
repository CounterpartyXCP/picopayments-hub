import unittest
import picopayments


PAYER_WIF = "cTbkqeNsCnzxWTTBZG47ZXaThthdNJ2cxkkDoHgsAgkmkVtGe8TJ"
PAYEE_WIF = "cMy2fuUBct1KhLo42yXovuhDFAM41SzrmsrAXTGoZ1fDS4HE1kX4"
PAYER_PUBKEY = picopayments.util.wif2pubkey(PAYER_WIF)
PAYEE_PUBKEY = picopayments.util.wif2pubkey(PAYEE_WIF)
SPEND_SECRET = (
    "f3e9e94cbaf2dd78346ec9b1a542bea78a6484decd8702e97df5f6b1928137df"
)
SPEND_SECRET_HASH = picopayments.util.hash160hex(SPEND_SECRET)


class TestScripts(unittest.TestCase):

    def test_get_deposit_payer_pubkey(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 1
        )
        pubkey = picopayments.scripts.get_deposit_payer_pubkey(script)
        self.assertEqual(pubkey, PAYER_PUBKEY)

    def test_get_deposit_payee_pubkey(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 1
        )
        pubkey = picopayments.scripts.get_deposit_payee_pubkey(script)
        self.assertEqual(pubkey, PAYEE_PUBKEY)

    def test_get_deposit_spend_secret_hash(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 1
        )
        h = picopayments.scripts.get_deposit_spend_secret_hash(script)
        self.assertEqual(h, SPEND_SECRET_HASH)

    def test_get_deposit_expire_time_min_op(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 1  # OP_1 (min)
        )
        t = picopayments.scripts.get_deposit_expire_time(script)
        self.assertEqual(t, 1)

    def test_get_deposit_expire_time_max_op(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 16  # OP_16
        )
        t = picopayments.scripts.get_deposit_expire_time(script)
        self.assertEqual(t, 16)

    def test_get_deposit_expire_time_min_data(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 17
        )
        t = picopayments.scripts.get_deposit_expire_time(script)
        self.assertEqual(t, 17)

    def test_get_deposit_expire_time_max_data(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH,
            picopayments.scripts.MAX_SEQUENCE
        )
        t = picopayments.scripts.get_deposit_expire_time(script)
        self.assertEqual(t, picopayments.scripts.MAX_SEQUENCE)

    def test_get_deposit_expire_time_over_max(self):
        script = picopayments.scripts.compile_deposit_script(
            PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH,
            picopayments.scripts.MAX_SEQUENCE + 1
        )

        def callback():
            picopayments.scripts.get_deposit_expire_time(script)
        self.assertRaises(ValueError, callback)


if __name__ == "__main__":
    unittest.main()
