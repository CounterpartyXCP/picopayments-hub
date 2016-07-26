# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


testnet = None  # loaded from args


# paths and files
root = None  # loaded from args
testnet_terms = "testnet.terms"
mainnet_terms = "mainnet.terms"
testnet_database = "testnet.db"
mainnet_database = "mainnet.db"
testnet_log = "testnet.log"
mainnet_log = "mainnet.log"


# server
host = None  # loaded from args
port = None  # loaded from args


# counterpartylib api
counterparty_url = None  # loaded from args
counterparty_username = None  # loaded from args
counterparty_password = None  # loaded from args


def load(args):
    globals()["testnet"] = args["testnet"]

    # paths and files
    globals()["root"] = args["root"]

    # server
    globals()["host"] = args["host"]
    globals()["port"] = args["port"]

    # counterpartylib api
    globals()["counterparty_url"] = args["cp_url"]
    globals()["counterparty_username"] = args["cp_username"]
    globals()["counterparty_password"] = args["cp_password"]
