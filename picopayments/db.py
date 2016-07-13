# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import apsw
from . import cfg


# old version -> migrate sql
_MIGRATIONS = {
    0: open('picopayments/sql/migration_0.sql').read(),
}

_GET_USERVERSION = 'PRAGMA user_version'
_SET_USERVERSION = 'PRAGMA user_version = {0}'
_GET_ASSET_KEYS = "SELECT * FROM Keys WHERE asset = :asset"
_GET_ALL_KEYS = "SELECT * FROM Keys"
_CNT_ASSET_KEYS = "SELECT :asset, count() FROM Keys WHERE asset = :asset"
_CNT_KEYS_PER_ASSET = "SELECT asset, count() FROM Keys GROUP BY asset"
_ADD_KEY = """
    INSERT INTO Keys (asset, pubkey, wif, address)
    VALUES (:asset, :pubkey, :wif, :address)
"""


_connection = None  # set in initialize


def _row_to_dict_factory(cursor, row):
    return {k[0]: row[i] for i, k in enumerate(cursor.getdescription())}


def _exec(sql, args=None):
    """Execute sql"""
    cursor = _connection.cursor()
    return cursor.execute(sql, args)


def _one(sql, args=None, asdict=True):
    """Execute sql and fetch one row."""
    cursor = _connection.cursor()
    if asdict:
        cursor.setrowtrace(_row_to_dict_factory)
    return cursor.execute(sql, args).fetchone()


def _all(sql, args=None, asdict=True):
    """Execute sql and fetch all rows."""
    cursor = _connection.cursor()
    if asdict:
        cursor.setrowtrace(_row_to_dict_factory)
    return cursor.execute(sql, args).fetchall()


def _migrate():
    db_version = _one(_GET_USERVERSION)["user_version"]
    while db_version in _MIGRATIONS:
        _exec(_MIGRATIONS[db_version])
        db_version += 1
        _exec(_SET_USERVERSION.format(db_version))


def initialize():
    db_file = cfg.testnet_database if cfg.testnet else cfg.mainnet_database
    db_path = os.path.join(cfg.root, db_file)
    if not os.path.exists(os.path.dirname(db_path)):  # ensure root path exists
        os.makedirs(os.path.dirname(db_path))
    globals()["_connection"] = apsw.Connection(db_path)
    _migrate()


def add_keys(keys):
    cursor = _connection.cursor()
    cursor.execute("BEGIN TRANSACTION")
    cursor.executemany(_ADD_KEY, keys)
    cursor.execute("COMMIT")


def count_keys(asset=None):
    if asset is not None:
        return dict(_all(_CNT_ASSET_KEYS, {"asset": asset}, asdict=False))
    else:
        return dict(_all(_CNT_KEYS_PER_ASSET, asdict=False))


def get_keys(asset=None):
    if asset is not None:
        return _all(_GET_ASSET_KEYS, {"asset": asset})
    else:
        return _all(_GET_ALL_KEYS)
