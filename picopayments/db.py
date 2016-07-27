# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import apsw
from . import cfg


def _sql(name):
    return open('picopayments/sql/{0}.sql'.format(name)).read()


# old version -> migrate sql
_MIGRATIONS = {
    0: _sql("migration_0"),
}
_HUB_CONNECTION = "SELECT * FROM HubConnection where handle = :handle"
_MICROPAYMENT_CHANNEL = "SELECT * FROM MicropaymentChannel WHERE id = :id"
_HANDLE_EXISTS = "SELECT EXISTS(SELECT * FROM HubConnection WHERE handle = ?);"
_UNNOTIFIED_PAYMENTS = _sql("unnotified_payments")
_UNNOTIFIED_COMMITS = _sql("unnotified_commits")
_UNNOTIFIED_REVOKES = _sql("unnotified_revokes")
_RECEIVE_CHANNEL = _sql("receive_channel")
_COMMITS_REQUESTED = _sql("commits_requested")
_COMMITS_ACTIVE = _sql("commits_active")
_COMMITS_REVOKED = _sql("commits_revoked")
_ADD_HUB_CONNECTION = _sql("add_hub_connection")
_ADD_REVOKE_SECRET = _sql("add_revoke_secret")
_ADD_KEY = _sql("add_key")
_ADD_PAYMENT = _sql("add_payment")
_ADD_COMMIT_REQUESTED = _sql("add_commit_requested")
_ADD_COMMIT_ACTIVE = _sql("add_commit_active")
_ADD_COMMIT_REVOKED = _sql("add_commit_revoked")
_RM_COMMITS = _sql("rm_commits")
_COMPLETE_HUB_CHANNELS = _sql("complete_hub_channels")
_SET_PAYMENT_NOTIFIED = _sql("set_payment_notified")
_SET_COMMIT_NOTIFIED = _sql("set_commit_notified")
_SET_REVOKE_NOTIFIED = _sql("set_revoke_notified")
_SET_NEXT_REVOKE_SECRET_HASH = _sql("set_next_revoke_secret_hash")


_connection = None  # set in setup


def _row_to_dict_factory(cursor, row):
    return {k[0]: row[i] for i, k in enumerate(cursor.getdescription())}


def get_cursor():
    return _connection.cursor()


def _exec(sql, args=None, cursor=None):
    """Execute sql"""
    cursor = cursor or get_cursor()
    cursor.execute(sql, args)


def _one(sql, args=None, asdict=True, cursor=None):
    """Execute sql and fetch one row."""
    cursor = cursor or get_cursor()
    if asdict:
        cursor.setrowtrace(_row_to_dict_factory)
    return cursor.execute(sql, args).fetchone()


def _all(sql, args=None, asdict=True, cursor=None):
    """Execute sql and fetch all rows."""
    cursor = cursor or get_cursor()
    if asdict:
        cursor.setrowtrace(_row_to_dict_factory)
    return cursor.execute(sql, args).fetchall()


def setup():

    # get db path
    db_file = cfg.testnet_database if cfg.testnet else cfg.mainnet_database
    db_path = os.path.join(cfg.root, db_file)

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
    db_version = _one("PRAGMA user_version;", cursor=cursor)["user_version"]
    while db_version in _MIGRATIONS:
        _exec(_MIGRATIONS[db_version], cursor=cursor)
        db_version += 1
        _exec("PRAGMA user_version = {0};".format(db_version), cursor=cursor)


def add_keys(keys, cursor=None):
    cursor = cursor or get_cursor()
    cursor.execute("BEGIN TRANSACTION")
    cursor.executemany(_ADD_KEY, keys)
    cursor.execute("COMMIT")


def hub_connection(handle, cursor=None):
    return _one(_HUB_CONNECTION, args={"handle": handle}, cursor=cursor)


def micropayment_channel(id, cursor=None):
    return _one(_MICROPAYMENT_CHANNEL, args={"id": id}, cursor=cursor)


def commits_requested(channel_id, cursor=None):
    args = {"channel_id": channel_id}
    entries = _all(_COMMITS_REQUESTED, args=args, cursor=cursor)
    return [entry["revoke_secret_hash"] for entry in entries]


def commits_active(channel_id, cursor=None):
    args = {"channel_id": channel_id}
    entries = _all(_COMMITS_ACTIVE, args=args, cursor=cursor)
    return [{"rawtx": e["rawtx"], "script": e["script"]} for e in entries]


def commits_revoked(channel_id, cursor=None):
    args = {"channel_id": channel_id}
    entries = _all(_COMMITS_REVOKED, args=args, cursor=cursor)
    return [
        {"script": e["script"], "revoke_secret": e["revoke_secret"]}
        for e in entries
    ]


def add_hub_connection(data, cursor=None):
    cursor = cursor or get_cursor()
    cursor.execute("BEGIN TRANSACTION")
    _exec(_ADD_HUB_CONNECTION, data, cursor=cursor)
    cursor.execute("COMMIT")


def complete_hub_connection(data, cursor=None):
    cursor = cursor or get_cursor()
    cursor.execute("BEGIN TRANSACTION")
    _exec(_SET_NEXT_REVOKE_SECRET_HASH, data, cursor=cursor)
    _exec(_COMPLETE_HUB_CHANNELS, data, cursor=cursor)
    add_revoke_secret_args = {
        "secret_hash": data["secret_hash"],
        "secret_value": data["secret_value"],
        "channel_id": data["recv_channel_id"],
    }
    _exec(_ADD_REVOKE_SECRET, args=add_revoke_secret_args, cursor=cursor)
    cursor.execute("COMMIT")


def handles_exist(handles, cursor=None):
    args = [(handle,) for handle in handles]
    cursor = cursor or get_cursor()
    result = cursor.executemany(_HANDLE_EXISTS, args).fetchall()
    return all([r[0] for r in result])


def set_next_revoke_secret_hash(handle, next_revoke_secret_hash, cursor=None):
    args = {
        "handle": handle,
        "next_revoke_secret_hash": next_revoke_secret_hash
    }
    _exec(_SET_NEXT_REVOKE_SECRET_HASH, args, cursor=cursor)


def add_payments(payments, cursor=None):
    cursor = cursor or get_cursor()
    cursor.executemany(_ADD_PAYMENT, payments)


def set_channel_state(channel_id, commits_requested, commits_active,
                      commits_revoked, cursor=None):
    cursor = cursor or get_cursor()
    cursor.execute(_RM_COMMITS, {"channel_id": channel_id})
    cursor.executemany(_ADD_COMMIT_REQUESTED, commits_requested)
    cursor.executemany(_ADD_COMMIT_ACTIVE, commits_requested)
    cursor.executemany(_ADD_COMMIT_REVOKED, commits_requested)


def unnotified_payments(handle):
    return _all(_UNNOTIFIED_PAYMENTS, {"payee_handle": handle})


def set_payments_notified(payment_ids, cursor=None):
    cursor = cursor or get_cursor()
    cursor.executemany(_SET_PAYMENT_NOTIFIED, payment_ids)


def unnotified_commit(channel_id, cursor=None):
    return _one(_UNNOTIFIED_COMMITS, {"channel_id": channel_id}, cursor=cursor)


def set_commit_notified(id, cursor=None):
    _exec(_SET_COMMIT_NOTIFIED, {"id": id}, cursor=cursor)


def unnotified_revokes(channel_id, cursor=None):
    return _all(_UNNOTIFIED_REVOKES, {"channel_id": channel_id}, cursor=cursor)


def set_revokes_notified(revoke_ids, cursor=None):
    cursor = cursor or get_cursor()
    cursor.executemany(_SET_REVOKE_NOTIFIED, revoke_ids)


def add_revoke_secret(channel_id, secret_hash, secret_value, cursor=None):
    args = {
        "channel_id": channel_id,
        "secret_hash": secret_hash,
        "secret_value": secret_value
    }
    _exec(_ADD_REVOKE_SECRET, args=args, cursor=cursor)


def receive_channel(handle, cursor=None):
    return _one(_RECEIVE_CHANNEL, args={"handle": handle}, cursor=cursor)
