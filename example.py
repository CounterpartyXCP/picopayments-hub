# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments.control import Control


asset = "A14456548018133352000"
control = Control(
    asset, user="rpc", password="1234", api_url="http://127.0.0.1:14000/api/",
    testnet=True, dryrun=True
)
funding_wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
src_address = control.btctxstore.get_address(funding_wif)


key = control.btctxstore.create_key()
dest_address = control.btctxstore.get_address(key)
print("{0} -> {1}".format(key, dest_address))
unsigned = control.create_tx(src_address, dest_address, 1337, 200000)
print(unsigned)
signed = control.btctxstore.sign_tx(unsigned, wifs=[funding_wif])
print(signed)


# Underfunded address
# wif: cPZmtXNUPwdsAjbowvAGEKLCqgQ38ZUu1DhFuQoeJoRdH6XWUwNX
# address:  mhNk2YmEkYNi8PVY86dPRr8z93CWQzXyAs
# A14456548018133352000: 1337
# BTC: 100000
