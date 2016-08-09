# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
from picopayments import config
from picopayments import cli
from picopayments import control
from picopayments import terms
from picopayments import __version__
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def main(args):

    # show version
    if "--version" in args:
        print(__version__)
        return

    # parse args and initialize
    parsed_args = cli.parse(args)
    control.initialize(parsed_args)

    # show configured terms
    if parsed_args["terms"]:
        print("Terms file saved at {0}".format(terms.path()))
        print(json.dumps(terms.read(), indent=2, sort_keys=True))
        return

    # show funding address for assets
    if parsed_args["funding"]:
        assets = terms.read().keys()
        addresses = control.create_funding_addresses(assets)
        print(json.dumps(addresses, indent=2, sort_keys=True))
        return

    # start server
    # FIXME optionally pass cert for ssl
    run_simple(
        config.host, config.port,
        application,
        processes=1,         # ensure db integrety, avoid race conditions
        ssl_context='adhoc'  # automatically create ssl context
    )
