# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os


testnet = None  # loaded from args
netcode = None  # loaded from args


# paths and files
path_database = None  # loaded from args
path_terms = None  # loaded from args
path_log = None  # loaded from args


# server
host = None  # loaded from args
port = None  # loaded from args


# counterpartylib api
counterparty_url = None  # loaded from args
counterparty_username = None  # loaded from args
counterparty_password = None  # loaded from args


# vars
database_connection = None  # set in db.setup


def load(args):
    testnet = args["testnet"]
    basedir = args["basedir"]
    database_file = "testnet.db" if testnet else "mainnet.db"
    terms_file = "testnet.terms" if testnet else "mainnet.terms"
    log_file = "testnet.log" if testnet else "mainnet.log"
    globals().update({

        "testnet": args["testnet"],
        "netcode": "XTN" if testnet else "BTC",

        # paths and files
        "basedir": basedir,

        # server
        "host": args["host"],
        "port": args["port"],

        # counterpartylib api
        "counterparty_url": args["cp_url"],
        "counterparty_username": args["cp_username"],
        "counterparty_password": args["cp_password"],

        # set paths
        "path_database": os.path.join(basedir, database_file),
        "path_terms": os.path.join(basedir, terms_file),
        "path_log": os.path.join(basedir, log_file),
    })
