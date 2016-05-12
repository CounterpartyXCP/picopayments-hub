# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments import util
from picopayments import scripts


class Base(util.UpdateThreadMixin):

    payer_wif = None            # wif
    payer_pubkey = None         # hex

    payee_wif = None            # wif
    payee_pubkey = None         # hex

    spend_secret = None         # hex

    deposit_script_hex = None   # hex
    deposit_rawtx = None        # hex

    timeout_rawtx = None        # hex
    change_rawtx = None         # hex

    # commit_rawtxs = []        # [rawtx]

    def save(self):
        with self.mutex:
            return {
                "payer_wif": self.payer_wif,
                "payer_pubkey": self.payer_pubkey,
                "payee_wif": self.payee_wif,
                "payee_pubkey": self.payee_pubkey,
                "spend_secret": self.spend_secret,
                "deposit_script_hex": self.deposit_script_hex,
                "deposit_rawtx": self.deposit_rawtx,
                "timeout_rawtx": self.timeout_rawtx,
                "change_rawtx": self.change_rawtx
            }

    def load(self, data):
        with self.mutex:
            self.payer_wif = data.get("payer_wif")
            self.payer_pubkey = data.get("payer_pubkey")
            self.payee_wif = data.get("payee_wif")
            self.payee_pubkey = data.get("payee_pubkey")
            self.spend_secret = data.get("spend_secret")
            self.deposit_script_hex = data.get("deposit_script_hex")
            self.deposit_rawtx = data.get("deposit_rawtx")
            self.timeout_rawtx = data.get("timeout_rawtx")
            self.change_rawtx = data.get("change_rawtx")

    def clear(self):
        with self.mutex:
            self.payer_wif = None
            self.payer_pubkey = None
            self.payee_wif = None
            self.payee_pubkey = None
            self.spend_secret = None
            self.deposit_script_hex = None
            self.deposit_rawtx = None
            self.timeout_rawtx = None
            self.change_rawtx = None

    def get_deposit_confirms(self):
        with self.mutex:
            assert(self.deposit_rawtx is not None)
            assert(self.deposit_script_hex is not None)
            txid = util.gettxid(self.deposit_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def get_timeout_confirms(self):
        with self.mutex:
            assert(self.timeout_rawtx is not None)
            txid = util.gettxid(self.timeout_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def get_change_confirms(self):
        with self.mutex:
            assert(self.change_rawtx is not None)
            txid = util.gettxid(self.change_rawtx)
            return self.control.btctxstore.confirms(txid) or 0

    def get_spend_secret_hash(self):
        if self.spend_secret is not None:  # payee
            return util.b2h(util.hash160(util.h2b(self.spend_secret)))
        elif self.deposit_script_hex is not None:  # payer
            script = util.h2b(self.deposit_script_hex)
            return scripts.get_deposit_spend_secret_hash(script)
        else:  # undefined
            raise Exception("Undefined state, not payee or payer.")

    def is_deposit_confirmed(self):
        with self.mutex:
            return self.get_deposit_confirms() > 0

    def is_deposit_expired(self):
        with self.mutex:
            script = util.h2b(self.deposit_script_hex)
            t = scripts.get_deposit_expire_time(script)
            return self.get_deposit_confirms() >= t

    def is_timeout_confirmed(self):
        with self.mutex:
            assert(self.timeout_rawtx is not None)
            txid = util.gettxid(self.timeout_rawtx)
            return bool(self.control.btctxstore.confirms(txid))

    def is_change_confirmed(self):
        with self.mutex:
            assert(self.change_rawtx is not None)
            txid = util.gettxid(self.change_rawtx)
            return bool(self.control.btctxstore.confirms(txid))

    def is_closing(self):
        return (
            self.change_rawtx is not None and not self.is_change_confirmed() or
            self.timeout_rawtx is not None and not self.is_timeout_confirmed()
        )

    def is_closed(self):
        return (
            self.change_rawtx is not None and self.is_change_confirmed() or
            self.timeout_rawtx is not None and self.is_timeout_confirmed()
        )

    def set_spend_secret(self, secret):
        self.spend_secret = secret
