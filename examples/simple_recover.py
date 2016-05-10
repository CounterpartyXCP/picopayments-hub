# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)

import json
# import time
import picopayments


channel = picopayments.channel.Payer(
    "A14456548018133352000", api_url="http://127.0.0.1:14000/api/",
    testnet=True, dryrun=True
)

# make initial deposit
payer_wif = "cUZoCj8cmBJBzuRFsBbyjRU2cjC2e9eu2B4KnGo1buxxZ8LKQYWq"

print(picopayments.util.b2h(picopayments.util.wif2sec(payer_wif)))

payee_pubkey = (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
)
spend_secret_hash = "a7ec62542b0d393d43442aadf8d55f7da1e303cb"
expire_time = 110
quantity = 1337
deposit_info = channel.deposit(
    payer_wif, payee_pubkey, spend_secret_hash, expire_time, quantity
)
print("DEPOSIT INFO:")
print(json.dumps(deposit_info, indent=2))


# while(channel.update() != "OPEN"):
#     time.sleep(1)


print("STATE:")
print(json.dumps(channel.save(), indent=2))
