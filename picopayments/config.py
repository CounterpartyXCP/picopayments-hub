# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


testnet = None  # loaded from args


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

    # set paths
    globals()["database"] = "testnet.db" if args["testnet"] else "mainnet.db"
    globals()["terms"] = "testnet.terms" if args[
        "testnet"] else "mainnet.terms"
