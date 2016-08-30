# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments import lib
from picopayments import cli
from picopayments import etc
from picopayments import __version__


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def main(args, serve=True):

    # show version
    if "--version" in args:
        print(__version__)
        return __version__

    # parse args and initialize
    parsed = cli.parse(args)
    lib.initialize(parsed)

    # show configured terms
    if parsed["terms"]:
        print("Terms file saved at {0}".format(etc.path_terms))
        terms = lib.terms()
        print(json.dumps(lib.terms(), indent=2, sort_keys=True))
        return terms

    # show funding address for assets
    if parsed["funding"]:
        assets = lib.terms().keys()
        addresses = lib.create_funding_addresses(assets)
        print(json.dumps(addresses, indent=2, sort_keys=True))
        return addresses

    if serve:

        # setup ssl
        ssl_context = 'adhoc'  # automatically create ssl context
        if parsed["ssl_cert_file"] and parsed["ssl_pkey_file"]:
            ssl_context = (parsed["ssl_cert_file"], parsed["ssl_pkey_file"])

        # start server
        run_simple(
            etc.host, etc.port,
            application,
            processes=1,  # ensure db integrety, avoid race conditions
            ssl_context=ssl_context
        )
