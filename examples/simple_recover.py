# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)

import time
import picopayments

# counterparty setup
api_url = "http://127.0.0.1:14000/api/"
asset = "A14456548018133352000"
testnet = True

# 0. Payee initializes channel as they wish to receive funds
payee_wif = "cQYT6HjZTUrniAb96s5ktjvGGZNBjbhd6SicC7s49RLcBBXmx3cz"
payee_channel = picopayments.channel.Payee(payee_wif, asset, api_url=api_url,
                                           testnet=testnet)

# 1. Payee gives payer spend secret hash and pubkey
payee_pubkey = payee_channel.get_pubkey()
spend_secret_hash = payee_channel.get_secret_hash()

# 2. Payer initializes channel with payee info
expire_time = 5  # payer chooses expire time
payer_wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
payer_channel = picopayments.channel.Payer(payer_wif, payee_pubkey,
                                           spend_secret_hash, expire_time,
                                           asset, api_url=api_url,
                                           testnet=testnet)

# 3. Payer opens channel by making a deposit
deposit_rawtx, deposit_script = payer_channel.deposit(31337)

# 4. Wait until deposit expired
while not payer_channel.is_deposit_expired():
    time.sleep(10)

# 5. Recover funds if no commit tx was published after 5 confirms
rawtx = payer_channel.recover()
txid = picopayments.util.gettxid(rawtx)
print(rawtx)
print(txid)
