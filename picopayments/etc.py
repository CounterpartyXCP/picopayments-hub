# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
from threading import RLock


# network
testnet = None  # loaded from args
netcode = None  # loaded from args


# paths and files
path_terms = None  # loaded from args
path_log = None  # loaded from args


# server
host = None  # loaded from args
port = None  # loaded from args


# counterparty
counterparty_url = None  # loaded from args
counterparty_username = None  # loaded from args
counterparty_password = None  # loaded from args


# database
database_path = None  # loaded from args
database_connection = None  # set in db.setup
database_lock = RLock()


# blockchain
confirms = 1
expire_clearance = 6  # only fund with x blocks clearance before expiration
delay_time = 2


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
        "database_path": os.path.join(basedir, database_file),
        "path_terms": os.path.join(basedir, terms_file),
        "path_log": os.path.join(basedir, log_file),
    })
