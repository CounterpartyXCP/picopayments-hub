# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


testnet = None  # loaded from args
netcode = None  # loaded from args


# paths and files
root = None  # loaded from args
database = None  # loaded from args
terms = None  # loaded from args


# server
host = None  # loaded from args
port = None  # loaded from args


# counterpartylib api
counterparty_url = None  # loaded from args
counterparty_username = None  # loaded from args
counterparty_password = None  # loaded from args


def load(args):
    globals().update({

        "testnet": args["testnet"],
        "netcode": "XTN" if args["testnet"] else "BTC",

        # paths and files
        "root": args["root"],

        # server
        "host": args["host"],
        "port": args["port"],

        # counterpartylib api
        "counterparty_url": args["cp_url"],
        "counterparty_username": args["cp_username"],
        "counterparty_password": args["cp_password"],

        # set paths
        "database": "testnet.db" if args["testnet"] else "mainnet.db",
        "terms": "testnet.terms" if args["testnet"] else "mainnet.terms",
    })
