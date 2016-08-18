# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import sys
import logging
from picopayments import cfg


FORMAT = "%(asctime)s %(levelname)s %(name)s %(lineno)d: %(message)s"
LEVEL_DEFAULT = logging.INFO
LEVEL_QUIET = 60
LEVEL_VERBOSE = logging.DEBUG


logging.basicConfig(format=FORMAT, level=LEVEL_DEFAULT)


def getLogger(name=None):
    formatter = logging.Formatter(FORMAT)

    # get log level
    if "--debug" in sys.argv or "--verbose" in sys.argv:
        level = LEVEL_VERBOSE  # full logging if --debug or --verbose arg given
    elif "--quiet" in sys.argv:
        level = LEVEL_QUIET  # no logging if --quite arg given
    else:
        level = LEVEL_DEFAULT

    # setup file handler
    fh = logging.FileHandler(cfg.path_log)
    fh.setFormatter(formatter)
    fh.setLevel(level)

    # setup stream handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(level)

    # setup logger
    logger = logging.getLogger(name=name)
    logger.setLevel(level)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


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
