import pycoin
import time
from threading import Thread
from pycoin.serialize import b2h  # NOQA
from pycoin.serialize import h2b  # NOQA
from pycoin.serialize import b2h_rev  # NOQA
from pycoin.encoding import hash160  # NOQA


def gettxid(rawtx):
    tx = pycoin.tx.Tx.from_hex(rawtx)
    return b2h_rev(tx.hash())


def wif2sec(wif):
    return pycoin.key.Key.from_text(wif).sec()


def wif2pubkey(wif):
    return b2h(wif2sec(wif))


def wif2address(wif):
    return pycoin.key.Key.from_text(wif).address()


def wif2secretexponent(wif):
    return pycoin.key.Key.from_text(wif).secret_exponent()


def pubkey2address(pubkey, netcode="BTC"):
    return sec2address(h2b(pubkey), netcode=netcode)


def sec2address(sec, netcode="BTC"):
    prefix = pycoin.networks.address_prefix_for_netcode(netcode)
    digest = pycoin.encoding.hash160(sec)
    return pycoin.encoding.hash160_sec_to_bitcoin_address(digest, prefix)


def script2address(script, netcode="BTC"):
    return pycoin.tx.pay_to.address_for_pay_to_script(script, netcode=netcode)


def hash160hex(hexdata):
    return b2h(hash160(h2b(hexdata)))


class UpdateThreadMixin(object):

    interval = 0.1
    _update_stop = False
    _update_thread = None

    def _update_target(self):
        last_call = 0
        while not self._update_stop:
            if (last_call + self.interval) < time.time():
                last_call = time.time()
                self.update()
            time.sleep(0.01)

    def start(self):
        self._update_thread = Thread(target=self._update_target)
        self._update_thread.start()

    def stop(self):
        if self._update_thread is not None:
            self._update_stop = True
            self._update_thread.join()
