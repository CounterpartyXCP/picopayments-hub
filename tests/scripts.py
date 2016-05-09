import unittest
import picopayments


SPEND_SECRET_HASH = "a7ec62542b0d393d43442aadf8d55f7da1e303cb"
SCRIPT_TEXT = (
    "OP_IF OP_2 0389bdba52b9820a4d672bbb14b6c01aa54963cc0f1419b14a01e9e"
    "beb62ebef1f 0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb8"
    "2f62490f75f8 OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 a7ec62"
    "542b0d393d43442aadf8d55f7da1e303cb OP_EQUALVERIFY 0389bdba52b9820a"
    "4d672bbb14b6c01aa54963cc0f1419b14a01e9ebeb62ebef1f OP_CHECKSIG OP_"
    "ELSE OP_5 OP_NOP3 OP_DROP 0389bdba52b9820a4d672bbb14b6c01aa54963cc"
    "0f1419b14a01e9ebeb62ebef1f OP_CHECKSIG OP_ENDIF OP_ENDIF"
)


class TestScripts(unittest.TestCase):

    def test_get_deposit_spend_secret_hash(self):
        h = picopayments.scripts.get_deposit_spend_secret_hash(SCRIPT_TEXT)
        self.assertEqual(h, SPEND_SECRET_HASH)


if __name__ == "__main__":
    unittest.main()
