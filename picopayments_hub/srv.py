# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import time
import threading
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from jsonrpc import JSONRPCResponseManager, dispatcher
from picopayments_hub import lib
from picopayments_hub import cli
from picopayments_hub import etc
from picopayments_hub import cron
from picopayments_hub import __version__


@Request.application
def application(request):
    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


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


def main(args, serve=True):

    # show version
    if "--version" in args:
        print(__version__)
        return __version__

    # parse args and initialize
    parsed = cli.parse(args)
    lib.initialize(parsed)

    if serve:
        return _start_server(parsed)
