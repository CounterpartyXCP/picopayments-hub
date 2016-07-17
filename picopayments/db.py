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

_GET_ASSET_KEYS = "SELECT * FROM Keys WHERE asset = :asset;"
_GET_ALL_KEYS = "SELECT * FROM Keys;"
_CNT_ASSET_KEYS = "SELECT :asset, count() FROM Keys WHERE asset = :asset;"
_CNT_KEYS_PER_ASSET = "SELECT asset, count() FROM Keys GROUP BY asset;"
_GET_HUB_CONNECTION = "SELECT * FROM HubConnection where handle = :handle"
_GET_MICROPAYMENT_CHANNEL = "SELECT * FROM MicropaymentChannel WHERE id = :id"

_ADD_KEY = """
    INSERT INTO Keys (asset, pubkey, wif, address)
    VALUES (:asset, :pubkey, :wif, :address);
"""

_sql = lambda file_path: open(file_path).read()

_ADD_HUB_CONNECTION = _sql("picopayments/sql/add_hub_connection.sql")
_COMPLETE_HUB_CONNECTION = _sql("picopayments/sql/complete_hub_connection.sql")

_connection = None  # set in setup


def _row_to_dict_factory(cursor, row):
    return {k[0]: row[i] for i, k in enumerate(cursor.getdescription())}


def _exec(sql, args=None):
    """Execute sql"""
    cursor = _connection.cursor()
    cursor.execute(sql, args)


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


def setup():

    # get db path
    db_file = cfg.testnet_database if cfg.testnet else cfg.mainnet_database
    db_path = os.path.join(cfg.root, db_file)

    # ensure root path exists
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))

    # get connection
    connection = apsw.Connection(db_path)

    # use foreign keys
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA defer_foreign_keys = ON;")

    # check foreign keys
    violations = list(cursor.execute("PRAGMA foreign_key_check;"))
    if violations:
        msg = "Foreign key check failed! {0}"
        raise Exception(msg.format(repr(violations)))

    # check integrity
    rows = cursor.execute("PRAGMA integrity_check;").fetchall()
    if not (len(rows) == 1 and rows[0][0] == "ok"):
        raise Exception("Integrity check failed!")

    # now ready for global use
    globals()["_connection"] = connection

    # migrate
    db_version = _one("PRAGMA user_version;")["user_version"]
    while db_version in _MIGRATIONS:
        _exec(_MIGRATIONS[db_version])
        db_version += 1
        _exec("PRAGMA user_version = {0};".format(db_version))


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


def get_hub_connection(handle):
    return _one(_GET_HUB_CONNECTION, args={"handle": handle})


def get_micropayment_channel(id):
    return _one(_GET_MICROPAYMENT_CHANNEL, args={"id": id})


def add_hub_connection(data):
    _exec(_ADD_HUB_CONNECTION, data)


def complete_hub_connection(data):
    _exec(_COMPLETE_HUB_CONNECTION, data)
