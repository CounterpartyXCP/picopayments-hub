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
    response = JSONRPCResponseManager.handle(
        request.data, dispatcher
    )  # pragma: no cover
    return Response(
        response.json, mimetype='application/json'
    )  # pragma: no cover


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
        addresses = lib.get_funding_addresses(assets)
        print(json.dumps(addresses, indent=2, sort_keys=True))
        return addresses

    if serve:

        # so internal calls skip http call
        etc.call_local_process = True  # pragma: no cover

        # setup ssl (generate pkey and self signed cert if none given)
        ssl_context = 'adhoc'  # pragma: no cover
        cert = parsed["ssl_cert_file"]  # pragma: no cover
        pkey = parsed["ssl_pkey_file"]  # pragma: no cover
        if cert and pkey:  # pragma: no cover
            ssl_context = (cert, pkey)  # pragma: no cover

        # start server
        run_simple(
            etc.host, etc.port,
            application,
            processes=1,  # ensure db integrety, avoid race conditions
            ssl_context=ssl_context
        )  # pragma: no cover
