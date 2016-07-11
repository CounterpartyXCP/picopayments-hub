import os
import argparse


def parse(args):

    description = "Decentral micropayment hub for counterparty assets."
    parser = argparse.ArgumentParser(description=description)

    # testnet
    parser.add_argument('--testnet', action='store_true',
                        help="Use bitcoin testnet instead of mainnet.")

    # counterparty user
    default = "rpc"
    msg = "Counterparty service username: {0}"
    parser.add_argument('--user', default=default, help=msg.format(default))

    # counterparty password
    default = "1234"
    msg = "Counterparty service password: {0}"
    parser.add_argument('--password', default=default, help=msg.format(default))

    # counterparty url
    default = "http://public.coindaddy.io:4000/api/"
    # testnet = "http://public.coindaddy.io:14000/api/"
    msg = "Counterparty service url: {0}"
    parser.add_argument('--url', default=default, help=msg.format(default))

    # database path
    default = os.path.join(os.path.expanduser("~"), ".picopayments.db")
    msg = "Picopayment database path: {0}"
    parser.add_argument('--database', default=default, help=msg.format(default))

    return vars(parser.parse_args(args=args))
