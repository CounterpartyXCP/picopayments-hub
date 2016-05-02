# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import pycoin


DEPOSIT_SCRIPT = """
    OP_IF
        2 {payer_pubkey} {payee_pubkey} 2 OP_CHECKMULTISIG
    OP_ELSE
        OP_IF
            OP_HASH160 {payee_secret_hash} OP_EQUALVERIFY
            {payer_pubkey} OP_CHECKSIG
        OP_ELSE
            {expire_time} OP_CHECKSEQUENCEVERIFY OP_DROP
            {payer_pubkey} OP_CHECKSIG
        OP_ENDIF
    OP_ENDIF
"""


COMMIT_SCRIPT = """
    OP_HASH160 {payee_secret_hash} OP_EQUALVERIFY {payee_pubkey} OP_CHECKSIG
"""


def compile_deposit_script(payer_pubkey, payee_pubkey,
                           recover_pubkey, expire_time):
    """
    Args:
        payer_pubkey (hexstr): TODO
        payee_pubkey (hexstr): TODO
        recover_pubkey (hexstr): TODO
        expire_time (int): TODO

    Return:
        Compiled bitcoin script.
    """
    script_text = DEPOSIT_SCRIPT.format(
        payer_pubkey=payer_pubkey,
        payee_pubkey=payee_pubkey,
        recover_pubkey=recover_pubkey,
        expire_time=str(expire_time)
    )
    return pycoin.tx.script.tools.compile(script_text)


def create_deposit_script(payer_sec, payee_sec, recover_sec, expire_time):
    return compile_deposit_script(pycoin.serialize.b2h(payer_sec),
                                  pycoin.serialize.b2h(payee_sec),
                                  pycoin.serialize.b2h(recover_sec),
                                  expire_time)


class ScriptMicropaymentChannel(pycoin.tx.pay_to.ScriptType.ScriptType):

    TEMPLATE = compile_deposit_script("OP_PUBKEY", "OP_PUBKEY", "OP_PUBKEY")

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
        result = db.get(pycoin.encoding.hash160(self.recover_sec))
        if result is not None:
            secret_exponent, public_pair, compressed = result
            sig = self._create_script_signature(secret_exponent, sign_value,
                                                signature_type)
            solution = pycoin.tx.script.tools.bin_script([sig])

        # TODO solve for refund case

        return solution

    def __repr__(self):
        script_text = pycoin.tx.script.tools.disassemble(self.script)
        return "<ScriptMicropaymentChannel: {0}".format(script_text)


# FIXME create decorater for this and commit to pycoin
# monkey patch pycoin pay to script subclassis with our own
pycoin.tx.pay_to.SUBCLASSES.insert(0, ScriptMicropaymentChannel)
