# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import picopayments


# counterparty setup
counterparty_url = "http://127.0.0.1:14000/api/"
asset = "A14456548018133352000"
testnet = True
dryrun = True


# payer (pub key must be on the blockchain, required by counterparty)
alice_wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"  # has funds
alice_sec = picopayments.util.wif2sec(alice_wif)
alice_address = picopayments.util.wif2address(alice_wif)
alice_channel = picopayments.channel.Payer(
    asset, counterparty_url=counterparty_url, testnet=testnet, dryrun=dryrun
)


# payee (pub key must be on the blockchain, required by counterparty)
bob_wif = "cQYT6HjZTUrniAb96s5ktjvGGZNBjbhd6SicC7s49RLcBBXmx3cz"
bob_sec = picopayments.util.wif2sec(bob_wif)
bob_address = picopayments.util.wif2address(bob_wif)
bob_channel = picopayments.channel.Payee(
    asset, counterparty_url=counterparty_url, testnet=testnet, dryrun=dryrun
)
