# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


testnet = None  # loaded from args


# paths and files
root = None  # loaded from args
testnet_terms = "testnet_terms.json"
mainnet_terms = "mainnet_terms.json"


# counterpartylib api
counterparty_url = None  # loaded from args
counterparty_username = None  # loaded from args
counterparty_password = None  # loaded from args


# server
host = None  # loaded from args
port = None  # loaded from args


def load(args):
    globals()["testnet"] = args["testnet"]
    globals()["root"] = args["root"]
    globals()["cp_url"] = args["cp_url"]
    globals()["cp_username"] = args["cp_username"]
    globals()["cp_password"] = args["cp_password"]
    globals()["host"] = args["host"]
    globals()["port"] = args["port"]
