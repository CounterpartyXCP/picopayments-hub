import sys
import logging
from . import config


FORMAT = "%(asctime)s %(levelname)s %(name)s %(lineno)d: %(message)s"
LEVEL_DEFAULT = logging.INFO
LEVEL_QUIET = logging.ERROR  # 60
LEVEL_VERBOSE = logging.DEBUG


logging.basicConfig(format=FORMAT, level=LEVEL_QUIET)


def getLogger(name=None):
    logger = logging.getLogger(name=name)
    formatter = logging.Formatter(FORMAT)
    fh = logging.FileHandler(config.path_log)
    fh.setFormatter(formatter)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # full logging if --debug or --verbose arg given
    if "--debug" in sys.argv or "--verbose" in sys.argv:
        logger.setLevel(LEVEL_VERBOSE)  # pragma: no cover
        fh.setLevel(LEVEL_VERBOSE)  # pragma: no cover
        ch.setLevel(LEVEL_VERBOSE)  # pragma: no cover

    # no logging if --quite arg given
    elif "--quiet" in sys.argv:
        logger.setLevel(LEVEL_QUIET)  # pragma: no cover
        fh.setLevel(LEVEL_QUIET)  # pragma: no cover
        ch.setLevel(LEVEL_QUIET)  # pragma: no cover

    # default to info
    else:
        logger.setLevel(LEVEL_DEFAULT)  # pragma: no cover
        fh.setLevel(LEVEL_DEFAULT)  # pragma: no cover
        ch.setLevel(LEVEL_DEFAULT)  # pragma: no cover

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
