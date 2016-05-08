# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments import util
from picopayments import scripts
from picopayments import exceptions
import logging


VALID_STATES = [
    "INITIALIZING",  # deposit not yet made
    "DEPOSITING",  # deposit published but not yet confirmed
    "OPEN",  # deposit made, confirmed but not commit tx ready
    "RECOVERING",  # recover tx published but not yet confirmed
    "CLOSED",  # no more funds in channel
]


_log = logging.getLogger(__name__)


class Base(util.UpdateThreadMixin):

    state = None                # str

    payer_wif = None            # wif
    payer_pubkey = None         # hex

    payee_wif = None            # wif
    payee_pubkey = None         # hex

    spend_secret = None         # hex
    spend_secret_hash = None    # hex

    deposit_expire_time = None  # int
    deposit_script_text = None  # disassembled script
    deposit_rawtx = None        # hex

    recover_rawtx = None        # hex

    # commit_rawtxs = []     # [rawtx]
    # change_rawtx = None

    def save(self):
        with self.mutex:
            return {
                "state": self.state,
                "payer_wif": self.payer_wif,
                "payer_pubkey": self.payer_pubkey,
                "payee_wif": self.payee_wif,
                "payee_pubkey": self.payee_pubkey,
                "spend_secret": self.spend_secret,
                "spend_secret_hash": self.spend_secret_hash,
                "deposit_expire_time": self.deposit_expire_time,
                "deposit_script_text": self.deposit_script_text,
                "deposit_rawtx": self.deposit_rawtx,
                "recover_rawtx": self.recover_rawtx
            }

    def load(self, data):
        with self.mutex:
            self.state = data["state"]
            self.payer_wif = data["payer_wif"]
            self.payer_pubkey = data["payer_pubkey"]
            self.payee_wif = data["payee_wif"]
            self.payee_pubkey = data["payee_pubkey"]
            self.spend_secret = data["spend_secret"]
            self.spend_secret_hash = data["spend_secret_hash"]
            self.deposit_expire_time = data["deposit_expire_time"]
            self.deposit_script_text = data["deposit_script_text"]
            self.deposit_rawtx = data["deposit_rawtx"]
            self.recover_rawtx = data["recover_rawtx"]

    def clear(self):
        with self.mutex:
            self.state = None
            self.payer_wif = None
            self.payer_pubkey = None
            self.payee_wif = None
            self.payee_pubkey = None
            self.spend_secret = None
            self.spend_secret_hash = None
            self.deposit_expire_time = None
            self.deposit_script_text = None
            self.deposit_rawtx = None
            self.recover_rawtx = None

    def _validate_state(self, expected):
        with self.mutex:
            assert(expected in VALID_STATES)
            if self.state != expected:
                raise exceptions.IllegalStateError(expected, self.state)

    def get_deposit_confirms(self):
        with self.mutex:
            assert(self.deposit_rawtx is not None)
            assert(self.deposit_script_text is not None)
            txid = util.gettxid(self.deposit_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def is_deposit_confirmed(self):
        with self.mutex:
            return self.get_deposit_confirms() > 0

    def is_deposit_expired(self):
        with self.mutex:
            deposit_expire_time = scripts.get_deposit_expire_time(
                self.deposit_script_text
            )
            return self.get_deposit_confirms() >= deposit_expire_time

    def is_recover_confirmed(self):
        with self.mutex:
            assert(self.recover_rawtx is not None)
            txid = util.gettxid(self.recover_rawtx)
            return bool(self.control.btctxstore.confirms(txid))

    def is_closed(self):
        with self.mutex:
            return self.state == "CLOSED"
