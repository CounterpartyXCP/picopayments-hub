# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)

import picopayments


# counterparty setup
counterparty_url = "http://127.0.0.1:14000/api/"
asset = "A14456548018133352000"
testnet = True
dryrun = True


# 0. Payee initializes channel as they wish to receive funds
payee_wif = "cQYT6HjZTUrniAb96s5ktjvGGZNBjbhd6SicC7s49RLcBBXmx3cz"
payee_channel = picopayments.channel.Payee(
    payee_wif, asset, counterparty_url=counterparty_url,
    testnet=testnet, dryrun=dryrun
)


# 1. Payee gives payer spend secret hash and pubkey
payee_pubkey = payee_channel.get_pubkey()
spend_secret_hash = payee_channel.get_secret_hash()
expire_time = 5  # 144 = 24h


# 2. Payer initializes channel with payee info
payer_wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
payer_channel = picopayments.channel.Payer(
    payer_wif, payee_pubkey, spend_secret_hash, expire_time, asset,
    counterparty_url=counterparty_url, testnet=testnet, dryrun=dryrun
)


# 3. Payer opens channel by making a deposit
deposit_rawtx, deposit_script = payer_channel.deposit(31337)
print(deposit_rawtx)
print()
print(deposit_script)
