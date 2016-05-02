import pycoin
import json
import requests
from btctxstore import BtcTxStore
from requests.auth import HTTPBasicAuth


DEFAULT_TESTNET = False
DEFAULT_COUNTERPARTY_RPC_MAINNET_URL = "http://public.coindaddy.io:4000/api/"
DEFAULT_COUNTERPARTY_RPC_TESTNET_URL = "http://public.coindaddy.io:14000/api/"
DEFAULT_COUNTERPARTY_RPC_USER = "rpc"
DEFAULT_COUNTERPARTY_RPC_PASSWORD = "1234"


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


def wif2sec(wif):
    return pycoin.key.Key.from_text(wif).sec()


def wif2address(wif):
    return pycoin.key.Key.from_text(wif).address()


def wif2secretexponent(wif):
    return pycoin.key.Key.from_text(wif).secret_exponent()


def sec2address(sec, netcode="BTC"):
    prefix = pycoin.networks.address_prefix_for_netcode(netcode)
    digest = pycoin.encoding.hash160(sec)
    return pycoin.encoding.hash160_sec_to_bitcoin_address(digest, prefix)


def script2address(script, netcode="BTC"):
    return pycoin.tx.pay_to.address_for_pay_to_script(script, netcode=netcode)


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


class Counterparty(object):

    def __init__(self, asset, user=DEFAULT_COUNTERPARTY_RPC_USER,
                 password=DEFAULT_COUNTERPARTY_RPC_PASSWORD, url=None,
                 testnet=DEFAULT_TESTNET):

        if testnet:
            self.url = DEFAULT_COUNTERPARTY_RPC_TESTNET_URL
        else:
            self.url = DEFAULT_COUNTERPARTY_RPC_MAINNET_URL
        self.testnet = testnet
        self.user = user
        self.password = password
        self.asset = asset
        self.netcode = "BTC" if not self.testnet else "XTN"
        self.btctxstore = BtcTxStore(testnet=self.testnet)

    def _rpc_call(self, payload):
        headers = {'content-type': 'application/json'}
        auth = HTTPBasicAuth(self.user, self.password)
        response = requests.post(self.url, data=json.dumps(payload),
                                 headers=headers, auth=auth)
        response_data = json.loads(response.text)
        if "result" not in response_data:
            raise Exception("Counterparty rpc call failed! {0}".format(
                repr(response)
            ))
        return response_data["result"]

    def _create_tx(self, source_address, dest_address, quantity):
        return self._rpc_call({
            "method": "create_send",
            "params": {
                "source": source_address,
                "destination": dest_address,
                "quantity": quantity,
                "asset": self.asset,
                # TODO "regular_dust_size" to ensur enough btc for refund fee
            },
            "jsonrpc": "2.0",
            "id": 0,
        })

    def get_balance(self, address):
        return self._rpc_call({
            "method": "get_balances",
            "params": {
                "filters": [
                    {'field': 'address', 'op': '==', 'value': address},
                    {'field': 'asset', 'op': '==', 'value': self.asset},
                ]
            },
            "jsonrpc": "2.0",
            "id": 0,
        })

    def deposit(self, payer_wif, payee_sec, quantity,
                expire_time, recover_sec=None):
        payer_sec = wif2sec(payer_wif)
        recover_sec = recover_sec or payer_sec
        script = create_deposit_script(payer_sec, payee_sec,
                                       recover_sec, expire_time)
        dest_address = script2address(script, self.netcode)
        payer_address = wif2address(payer_wif)
        rawtx = self._create_tx(payer_address, dest_address, quantity)
        signed_rawtx = self.btctxstore.sign_tx(rawtx, [payer_wif])
        return signed_rawtx, script

    def recover(self, recover_wif, script, quantity, expire_time):
        # TODO remove quantity and send all assets to recover address
        # TODO get expire_time from script

        # create recover tx
        channel_address = script2address(script, self.netcode)
        recover_address = wif2address(recover_wif)
        rawtx = self._create_tx(channel_address, recover_address, quantity)

        # prep for script compliance and signing
        tx = pycoin.tx.Tx.from_hex(rawtx)
        tx.version = 2  # enable relative lock-time, see bip68 & bip112
        for txin in tx.txs_in:
            txin.sequence = expire_time
            utxo_tx = self.btctxstore.service.get_tx(txin.previous_hash)
            tx.unspents.append(utxo_tx.txs_out[txin.previous_index])

        # sign
        secret_exponent = wif2secretexponent(recover_wif)
        hash160_lookup = pycoin.tx.pay_to.build_hash160_lookup(
            [secret_exponent]
        )
        p2sh_lookup = pycoin.tx.pay_to.build_p2sh_lookup([script])
        tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup)

        assert(tx.bad_signature_count() == 0)
        return tx.as_hex()
