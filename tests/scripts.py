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


ALPHA_SCRIPT = picopayments.scripts.compile_deposit_script(
    PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 1  # OP_1 (min)
)
BETA_SCRIPT = picopayments.scripts.compile_deposit_script(
    PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 16  # OP_16
)
GAMMA_SCRIPT = picopayments.scripts.compile_deposit_script(
    PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 17
)
DELTA_SCRIPT = picopayments.scripts.compile_deposit_script(
    PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 2 ** 8
)
EPSILON_SCRIPT = picopayments.scripts.compile_deposit_script(
    PAYER_PUBKEY, PAYEE_PUBKEY, SPEND_SECRET_HASH, 2**16
)


class TestScripts(unittest.TestCase):

    def test_get_deposit_spend_secret_hash(self):
        h = picopayments.scripts.get_deposit_spend_secret_hash(ALPHA_SCRIPT)
        self.assertEqual(h, SPEND_SECRET_HASH)

    def test_get_deposit_expire_time(self):
        t = picopayments.scripts.get_deposit_expire_time(ALPHA_SCRIPT)
        self.assertEqual(t, 1)
        t = picopayments.scripts.get_deposit_expire_time(BETA_SCRIPT)
        self.assertEqual(t, 16)
        t = picopayments.scripts.get_deposit_expire_time(GAMMA_SCRIPT)
        self.assertEqual(t, 17)
        t = picopayments.scripts.get_deposit_expire_time(DELTA_SCRIPT)
        self.assertEqual(t, 2 ** 8)
        t = picopayments.scripts.get_deposit_expire_time(EPSILON_SCRIPT)
        self.assertEqual(t, 2 ** 16)


if __name__ == "__main__":
    unittest.main()
