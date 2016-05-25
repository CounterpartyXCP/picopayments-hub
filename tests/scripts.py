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

PAYOUT_RAWTX = (
    "0200000001391814005e1098bcf161b8380923041dafef9e4a06578ffa4ccf06477f4f"
    "4da400000000e6473044022062bef3f4b21cd53dc248e08f9bb92021c7800d43f86a17"
    "ee7eaf044b2b0f51af02201d84bcca4356f77f5c20e12fac4b959c1d9362e8d0a41efe"
    "7165b5375518252a01201e23f27be91c610ea4286344f9f19adca1994afa522e15afd8"
    "b0cba404e17c7b514c7a6355b275a914050e1310e92253efc8cfb498d8e3594ec69f18"
    "098821028666087223829e3932b648e42df2caac57ce677f36ded247dd0cd7c1b229d0"
    "5bac67a914f7dc060ff00dfed0975bb0b3815c34898203bacb882102224b63a140724d"
    "d08fa6818ec1cda07f7e5e746d5ae865dc6e72c0970b0a1bb1ac680500000002361500"
    "00000000001976a914900729789e53c5fb566e400e3e03c88b0703bc5a88ac00000000"
    "000000001e6a1ce7299f7bdbc46197ae28018744dd7c9fc06b4778cf0b95a41f30ef53"
    "00000000"
)
SPEND_SECRET = (
    "1e23f27be91c610ea4286344f9f19adca1994afa522e15afd8b0cba404e17c7b"
)
COMMIT_SCRIPT = (
    "6355b275a914050e1310e92253efc8cfb498d8e3594ec69f1809882102"
    "8666087223829e3932b648e42df2caac57ce677f36ded247dd0cd7c1b2"
    "29d05bac67a914f7dc060ff00dfed0975bb0b3815c34898203bacb8821"
    "02224b63a140724dd08fa6818ec1cda07f7e5e746d5ae865dc6e72c097"
    "0b0a1bb1ac68"
)
print(PAYOUT_RAWTX)


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

    def test_get_spend_secret(self):
        secret = picopayments.scripts.get_spend_secret(
            PAYOUT_RAWTX, picopayments.util.h2b(COMMIT_SCRIPT)
        )
        self.assertEqual(secret, SPEND_SECRET)


if __name__ == "__main__":
    unittest.main()
