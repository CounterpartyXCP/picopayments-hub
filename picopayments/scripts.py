# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from pycoin.serialize import b2h
from pycoin import encoding
from pycoin.tx.script import tools
from pycoin.tx.pay_to.ScriptType import ScriptType
from pycoin.tx.pay_to import SUBCLASSES


DEFAULT_EXPIRE_TIME = 5
DEPOSIT_SCRIPT = """
    OP_IF
        2 {payer_pubkey} {payee_pubkey} 2 OP_CHECKMULTISIG
    OP_ELSE
        OP_IF
            OP_HASH160 {spend_secret_hash} OP_EQUALVERIFY
            {payer_pubkey} OP_CHECKSIG
        OP_ELSE
            {expire_time} OP_NOP3 OP_DROP
            {payer_pubkey} OP_CHECKSIG
        OP_ENDIF
    OP_ENDIF
"""


COMMIT_SCRIPT = """
    OP_IF
        OP_HASH160 {spend_secret_hash} OP_EQUALVERIFY
        {payee_pubkey} OP_CHECKSIG
    OP_ELSE
        OP_HASH160 {revoke_secret_hash} OP_EQUALVERIFY
        {payer_pubkey} OP_CHECKSIG
    OP_ENDIF
"""


def compile_deposit_script(payer_pubkey, payee_pubkey,
                           spend_secret_hash, expire_time):
    """
    Args:
        payer_pubkey (hexstr): TODO
        payee_pubkey (hexstr): TODO
        spend_secret_hash (hexstr): TODO
        expire_time (int): TODO

    Return:
        Compiled bitcoin script.
    """
    script_text = DEPOSIT_SCRIPT.format(
        payer_pubkey=payer_pubkey,
        payee_pubkey=payee_pubkey,
        spend_secret_hash=spend_secret_hash,
        expire_time=str(expire_time)
    )
    return tools.compile(script_text)


def create_deposit_script(payer_sec, payee_sec, recover_sec,
                          spend_secret_hash, expire_time):

    return compile_deposit_script(b2h(payer_sec), b2h(payee_sec),
                                  spend_secret_hash, expire_time)


class ScriptMicropaymentChannel(ScriptType):

    TEMPLATE = compile_deposit_script("OP_PUBKEY", "OP_PUBKEY",
                                      "OP_PUBKEYHASH", DEFAULT_EXPIRE_TIME)

    def __init__(self, payer_sec, payee_sec, recover_sec):
        self.payer_sec = payer_sec
        self.payee_sec = payee_sec
        self.recover_sec = recover_sec
        self.script = create_deposit_script(payer_sec, payee_sec, recover_sec)

    @classmethod
    def from_script(cls, script):
        r = cls.match(script)
        if r:
            payer_sec, payee_sec, recover_sec = r["PUBKEY_LIST"]
            obj = cls(payer_sec, payee_sec, recover_sec)
            assert(obj.script == script)
            return obj
        raise ValueError("bad script")

    def solve(self, **kwargs):
        db = kwargs.get("hash160_lookup")
        sign_value = kwargs.get("sign_value")
        signature_type = kwargs.get("signature_type")
        if db is None or sign_value is None or signature_type is None:
            raise Exception("Missing parameters!")

        # solve for recover case
        result = db.get(encoding.hash160(self.recover_sec))
        if result is not None:
            secret_exponent, public_pair, compressed = result
            sig = self._create_script_signature(secret_exponent, sign_value,
                                                signature_type)
            solution = tools.bin_script([sig])

        # TODO solve for refund case

        return solution

    def __repr__(self):
        script_text = tools.disassemble(self.script)
        return "<ScriptMicropaymentChannel: {0}".format(script_text)


# FIXME create decorater for this and commit to pycoin
# monkey patch pycoin pay to script subclassis with our own
SUBCLASSES.insert(0, ScriptMicropaymentChannel)
