# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments import config
from picopayments import cli
from picopayments import control
from picopayments import __version__
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


def main(args):

    # display version
    if "--version" in args:
        print(__version__)

    # parse args and initialize
    parsed_args = cli.parse(args)
    control.initialize(parsed_args)

    # display funding address for asset
    asset = parsed_args["fund_address"]  # FIXME validate input
    if asset is not None:
        print(control.create_funding_address(asset))

    # start server
    else:
        # FIXME optionally pass cert for ssl
        run_simple(
            config.host, config.port,
            application,
            processes=1,         # ensure db integrety, avoid race conditions
            ssl_context='adhoc'  # automatically create ssl context
        )
