# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import json
import traceback
from . import cli
from . import control
from . import terms
from . import config
from . import __version__
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
    parsed = cli.parse(args)
    control.initialize(parsed)

    # show configured terms
    if parsed["terms"]:
        print("Terms file saved at {0}".format(terms.path()))
        print(json.dumps(terms.read(), indent=2, sort_keys=True))
        return

    # show funding address for assets
    if parsed["funding"]:
        assets = terms.read().keys()
        addresses = control.create_funding_addresses(assets)
        print(json.dumps(addresses, indent=2, sort_keys=True))
        return

    # setup ssl
    ssl_context = 'adhoc'  # automatically create ssl context
    if parsed["ssl_cert_file"] and parsed["ssl_pkey_file"]:
        ssl_context = (parsed["ssl_cert_file"], parsed["ssl_pkey_file"])

    # start server
    run_simple(
        config.host, config.port,
        application,
        processes=1,  # ensure db integrety, avoid race conditions
        ssl_context=ssl_context
    )
