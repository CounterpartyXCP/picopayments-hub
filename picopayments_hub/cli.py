# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import argparse


def parse(args):

    # pre parse testnet to modify defaults depending on network
    testnet = "--testnet" in args

    description = "Decentral micropayment hub for counterparty assets."
    parser = argparse.ArgumentParser(description=description)

    # network to use
    parser.add_argument(
        '--testnet', action='store_true', help="Use bitcoin testnet."
    )

    # show version
    parser.add_argument(
        '--version', action='store_true', help="Show version number."
    )

    # basedir path
    default = os.path.join(os.path.expanduser("~"), ".picopayments")
    parser.add_argument(
        '--basedir', default=default, metavar="PATH",
        help="Location of app files: {0}".format(default)
    )

    # server
    parser.add_argument(
        '--host', default="localhost", metavar="PORT",
        help="Server host: {0}".format("localhost")
    )
    default = 15000 if testnet else 5000
    parser.add_argument(
        '--port', type=int, default=default, metavar="PORT",
        help="Server port: {0}".format(default)
    )
    parser.add_argument(
        '--ssl_cert_file', default=None, metavar="PATH",
        help="Path to ssl certificate file."
    )
    parser.add_argument(
        '--ssl_pkey_file', default=None, metavar="PATH",
        help="Path to ssl private key file."
    )

    # counterpartylib api
    default_port = 14000 if testnet else 4000
    default = "http://public.coindaddy.io:{0}/api/".format(default_port)
    parser.add_argument(
        '--cp_url', default=default, metavar="URL",
        help="Counterparty api: {0}".format(default)
    )
    parser.add_argument(
        '--cp_username', default="rpc", metavar="VALUE",
        help="Counterparty username: {0}".format("rpc")
    )
    parser.add_argument(
        '--cp_password', default="1234", metavar="VALUE",
        help="Counterparty password: {0}".format("1234")
    )

    return vars(parser.parse_args(args=args))
