# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from pycoin.serialize import b2h, h2b
from pycoin import encoding
from pycoin.tx.script import tools
from pycoin.tx.pay_to.ScriptType import ScriptType
from pycoin.tx.pay_to import SUBCLASSES
from pycoin.encoding import hash160
from pycoin.tx.pay_to.ScriptType import DEFAULT_PLACEHOLDER_SIGNATURE


MAX_SEQUENCE = 0x0000FFFF
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
        {delay_time} OP_NOP3 OP_DROP
        OP_HASH160 {spend_secret_hash} OP_EQUALVERIFY
        {payee_pubkey} OP_CHECKSIG
    OP_ELSE
        OP_HASH160 {revoke_secret_hash} OP_EQUALVERIFY
        {payer_pubkey} OP_CHECKSIG
    OP_ENDIF
"""


def get_word(script, index):
    pc = 0
    i = 0
    while pc < len(script) and i <= index:
        opcode, data, pc = tools.get_opcode(script, pc)
        i += 1
    if i != index + 1:
        raise ValueError(index)
    return opcode, data, tools.disassemble_for_opcode_data(opcode, data)


def parse_sequence_value(opcode, data, disassembled):
    value = None
    if opcode == 0:
        value = 0
    elif 0 < opcode < 76:  # get from data bytes
        value = tools.int_from_script_bytes(data)
    elif 80 < opcode < 97:  # OP_1 - OP_16
        value = opcode - 80
    else:
        raise ValueError("Invalid expire time: {0}".format(disassembled))
    if value > MAX_SEQUENCE:
        msg = "Max expire time exceeded: {0} > {1}"
        raise ValueError(msg.format(value, MAX_SEQUENCE))
    return value


def get_commit_payer_pubkey(script):
    opcode, data, disassembled = get_word(script, 13)
    return b2h(data)


def get_commit_payee_pubkey(script):
    opcode, data, disassembled = get_word(script, 7)
    return b2h(data)


def get_commit_delay_time(script):
    opcode, data, disassembled = get_word(script, 1)
    return parse_sequence_value(opcode, data, disassembled)


def get_commit_spend_secret_hash(script):
    opcode, data, disassembled = get_word(script, 5)
    return b2h(data)


def get_commit_revoke_secret_hash(script):
    opcode, data, disassembled = get_word(script, 11)
    return b2h(data)


def get_deposit_payer_pubkey(script):
    opcode, data, disassembled = get_word(script, 2)
    return b2h(data)


def get_deposit_payee_pubkey(script):
    opcode, data, disassembled = get_word(script, 3)
    return b2h(data)


def get_deposit_expire_time(script):
    opcode, data, disassembled = get_word(script, 14)
    return parse_sequence_value(opcode, data, disassembled)


def get_deposit_spend_secret_hash(script):
    opcode, data, disassembled = get_word(script, 9)
    return b2h(data)


def compile_deposit_script(payer_pubkey, payee_pubkey,
                           spend_secret_hash, expire_time):
    """Compile deposit transaction pay ot script.

    Args:
        payer_pubkey: Hex encoded public key in sec format.
        payee_pubkey: Hex encoded public key in sec format.
        spend_secret_hash: Hex encoded hash160 of spend secret.
        expire_time: Channel expire time in blocks given as int.

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


def compile_commit_script(payer_pubkey, payee_pubkey, spend_secret_hash,
                          revoke_secret_hash, delay_time):
    script_text = COMMIT_SCRIPT.format(
        payer_pubkey=payer_pubkey,
        payee_pubkey=payee_pubkey,
        spend_secret_hash=spend_secret_hash,
        revoke_secret_hash=revoke_secret_hash,
        delay_time=str(delay_time)
    )
    return tools.compile(script_text)


class AbsScriptChannelDeposit(ScriptType):

    def __init__(self, payer_sec, payee_sec, spend_secret_hash, expire_time):
        self.payer_sec = payer_sec
        self.payee_sec = payee_sec
        self.spend_secret_hash = spend_secret_hash
        self.expire_time = expire_time
        self.script = compile_deposit_script(b2h(payer_sec), b2h(payee_sec),
                                             spend_secret_hash, expire_time)

    @classmethod
    def from_script(cls, script):
        r = cls.match(script)
        if r:
            payer_sec = r["PUBKEY_LIST"][0]
            payee_sec = r["PUBKEY_LIST"][1]
            assert(payer_sec == r["PUBKEY_LIST"][2])
            assert(payer_sec == r["PUBKEY_LIST"][3])
            spend_secret_hash = b2h(r["PUBKEYHASH_LIST"][0])
            expire_time = get_deposit_expire_time(cls.TEMPLATE)
            obj = cls(payer_sec, payee_sec, spend_secret_hash, expire_time)
            assert(obj.script == script)
            return obj
        raise ValueError("bad script")

    def solve(self, **kwargs):
        hash160_lookup = kwargs["hash160_lookup"]
        signature_type = kwargs["signature_type"]
        sign_value = kwargs["sign_value"]
        spend_secret = kwargs["spend_secret"]
        spend_type = kwargs["spend_type"]

        signature_placeholder = kwargs.get("signature_placeholder",
                                           DEFAULT_PLACEHOLDER_SIGNATURE)

        # get signing key
        if spend_type == "finalize_commit":
            private_key = hash160_lookup.get(encoding.hash160(self.payee_sec))
        else:
            private_key = hash160_lookup.get(encoding.hash160(self.payer_sec))

        secret_exponent, public_pair, compressed = private_key
        sig = self._create_script_signature(secret_exponent, sign_value,
                                            signature_type)
        if spend_type == "timeout":
            script_sig = "{sig} OP_0 OP_0".format(sig=b2h(sig))
        elif spend_secret is not None:  # change tx
            spend_secret_hash = get_deposit_spend_secret_hash(self.script)
            provided_spend_secret_hash = b2h(hash160(h2b(spend_secret)))
            assert(spend_secret_hash == provided_spend_secret_hash)
            script_sig = "{sig} {secret} OP_1 OP_0".format(
                sig=b2h(sig), secret=spend_secret
            )
        elif spend_type == "create_commit":
            script_sig = "{payer_sig} {payee_sig} OP_1".format(
                payer_sig=b2h(sig), payee_sig=b2h(signature_placeholder)
            )
        elif spend_type == "finalize_commit":

            # extract payer sig
            existing_script = kwargs.get("existing_script")
            opcode, payer_sig, text = get_word(existing_script, 0)

            script_sig = "{payer_sig} {payee_sig} OP_1".format(
                payer_sig=b2h(payer_sig), payee_sig=b2h(sig)
            )
        else:
            raise Exception("Illegal State!")
        return tools.compile(script_sig)

    def __repr__(self):
        script_text = tools.disassemble(self.script)
        return "<ScriptChannelDeposit: {0}".format(script_text)


class DepositScriptHandler():

    def __init__(self, expire_time):
        class ScriptChannelDeposit(AbsScriptChannelDeposit):
            TEMPLATE = compile_deposit_script(
                "OP_PUBKEY", "OP_PUBKEY",
                "OP_PUBKEYHASH", expire_time
            )
        self.script_handler = ScriptChannelDeposit

    def __enter__(self):
        SUBCLASSES.insert(0, self.script_handler)

    def __exit__(self, type, value, traceback):
        SUBCLASSES.pop(0)
