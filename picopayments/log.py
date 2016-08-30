# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import sys
import logging
from picopayments import etc


# FORMAT = "%(asctime)s %(levelname)s %(name)s %(lineno)d: %(message)s"
FORMAT = "%(asctime)s %(levelname)s: %(message)s"
LEVEL_DEFAULT = logging.INFO
LEVEL_QUIET = 60
LEVEL_VERBOSE = logging.DEBUG


# silence global logger
logging.basicConfig(format=FORMAT, level=LEVEL_QUIET)


def getLogger(suffix=None, name=None):
    level = LEVEL_DEFAULT

    # full logging if --debug or --verbose arg given
    if "--debug" in sys.argv or "--verbose" in sys.argv:
        level = LEVEL_VERBOSE  # pragma: no cover

    # no logging if --quite arg given
    elif "--quiet" in sys.argv:
        level = LEVEL_QUIET  # pragma: no cover

    # setup file handler
    fh = logging.FileHandler(etc.path_log)
    fh.setFormatter(logging.Formatter(FORMAT))
    fh.setLevel(level)

    # setup logger
    base = logging.getLogger()
    child = base.getChild(name or suffix or "Default")
    child.setLevel(level)
    child.addHandler(fh)
    return child


def debug(msg, *args, **kwargs):
    getLogger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    getLogger().info(msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    getLogger().warn(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    getLogger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    getLogger().critical(msg, *args, **kwargs)


def fatal(msg, *args, **kwargs):
    getLogger().fatal(msg, *args, **kwargs)
