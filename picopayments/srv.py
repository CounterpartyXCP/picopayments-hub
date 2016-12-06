# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import time
import json
import threading
from collections import defaultdict
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments import lib
from picopayments import cli
from picopayments import db
from picopayments import etc
from picopayments import cron
from picopayments import __version__


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def _show_terms():
    print("Terms file saved at {0}".format(etc.path_terms))
    terms = lib.terms()
    print(json.dumps(lib.terms(), indent=2, sort_keys=True))
    return terms


def _show_funding():
    assets = lib.terms().keys()
    addresses = lib.get_funding_addresses(assets)
    print(json.dumps(addresses, indent=2, sort_keys=True))
    return addresses


def _ssl_context(parsed):
    # setup ssl (generate pkey and self signed cert if none given)
    ssl_context = 'adhoc'
    cert = parsed["ssl_cert_file"]
    pkey = parsed["ssl_pkey_file"]
    if cert and pkey:
        ssl_context = (cert, pkey)
    return ssl_context


_stop_cron_flag = threading.Event()


def _cron_loop():
    while not _stop_cron_flag.isSet():
        cron.run_all()
        time.sleep(10)


def _start_server(parsed):
    try:
        thread = threading.Thread(target=_cron_loop)
        thread.start()

        run_simple(
            etc.host, etc.port,
            application,
            processes=1,  # ensure db integrety, avoid race conditions
            ssl_context=_ssl_context(parsed)
        )
    finally:
        _stop_cron_flag.set()
        thread.join()


def _show_balances():
    """Show total and individual balances (confirmed only)."""
    result = {
        "total": defaultdict(lambda: 0),
        "addresses": defaultdict(lambda: []),
    }
    for asset in lib.terms().keys():
        for key in db.keys(asset=asset):
            balances = lib.get_balances(
                key["address"], assets=["BTC", key["asset"]]
            )
            for asset, quantity in balances.items():
                result["total"][asset] += quantity
            result["addresses"][key["asset"]].append({
                "address": key["address"],
                "balances": balances
            })

    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def _show_connections():
    # FIXME limet to only opening|connected|closed
    connections = []
    for hub_conn in db.hub_connections_all():
        connections.append(lib.get_status(hub_conn))
    print(json.dumps(connections, indent=2, sort_keys=True))
    return connections


def main(args, serve=True):

    # show version
    if "--version" in args:
        print(__version__)
        return __version__

    # parse args and initialize
    parsed = cli.parse(args)
    lib.initialize(parsed)

    if parsed["terms"]:
        return _show_terms()
    if parsed["balances"]:
        return _show_balances()
    if parsed["connections"]:
        return _show_connections()
    if parsed["funding"]:
        return _show_funding()
    if serve:
        return _start_server(parsed)
