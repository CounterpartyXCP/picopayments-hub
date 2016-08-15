# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import apsw
import pkg_resources
from threading import RLock
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments import scripts
from . import cfg


def _sql(name):
    sql_path = os.path.join("sql", "{0}.sql".format(name))
    sql = pkg_resources.resource_stream("picopayments", sql_path).read()
    return sql.decode("utf-8")


# old version -> migrate sql
_MIGRATIONS = {
    0: _sql("migration_0"),
}
_HUB_CONNECTION = "SELECT * FROM HubConnection where handle = :handle"
_MICROPAYMENT_CHANNEL = "SELECT * FROM MicropaymentChannel WHERE id = :id"
_HANDLE_EXISTS = "SELECT EXISTS(SELECT * FROM HubConnection WHERE handle = ?);"
_CONNECTION_TERMS = "SELECT * FROM Terms WHERE id = :id;"
_KEY = "SELECT * FROM Keys WHERE pubkey = :pubkey;"
_CHANNEL_PAYER_KEY = _sql("channel_payer_key")
_UNNOTIFIED_PAYMENTS = _sql("unnotified_payments")
_UNNOTIFIED_COMMITS = _sql("unnotified_commits")
_UNNOTIFIED_REVOKES = _sql("unnotified_revokes")
_RECEIVE_CHANNEL = _sql("receive_channel")
_SEND_PAYMENTS_SUM = _sql("send_payments_sum")
_RECV_PAYMENTS_SUM = _sql("recv_payments_sum")
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


lock = RLock()
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
    db_path = os.path.join(cfg.basedir, cfg.database)

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
        "handle": handle, "next_revoke_secret_hash": next_revoke_secret_hash
    }
    _exec(_SET_NEXT_REVOKE_SECRET_HASH, args, cursor=cursor)


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


def connection_terms(terms_id, cursor=None):
    return _one(_CONNECTION_TERMS, args={"id": terms_id}, cursor=cursor)


def load_channel_state(channel_id, asset, cursor=None):
    channel = micropayment_channel(channel_id, cursor=cursor)
    state = {}
    state["asset"] = asset
    state["deposit_script"] = channel["deposit_script"]
    state["commits_requested"] = commits_requested(
        channel_id, cursor=cursor
    )
    state["commits_active"] = commits_active(channel_id, cursor=cursor)
    state["commits_revoked"] = commits_revoked(channel_id, cursor=cursor)
    return state


def _fmt_requested(channel_id, revoke_secret_hashes):
    requested = []
    for revoke_secret_hash in revoke_secret_hashes:
        requested.append({
            "channel_id": channel_id,
            "revoke_secret_hash": revoke_secret_hash
        })
    return requested


def _script_data(script):
    delay_time = scripts.get_commit_delay_time(util.h2b(script))
    secret_hash = scripts.get_commit_revoke_secret_hash(util.h2b(script))
    commit_address = util.script2address(util.h2b(script),
                                         netcode=cfg.netcode)
    return {
        "commit_address": commit_address,
        "delay_time": delay_time,
        "revoke_secret_hash": secret_hash,
    }


def _fmt_active(channel_id, unnotified_commit, commits_active):
    active = []
    for commit_active in commits_active:
        script = commit_active["script"]
        rawtx = commit_active["rawtx"]

        payee_notified = 1
        if unnotified_commit and unnotified_commit["script"] == script:
            payee_notified = 0

        data = {
            "channel_id": channel_id,
            "script": script,
            "rawtx": rawtx,
            "payee_notified": payee_notified
        }
        data.update(_script_data(script))
        active.append(data)
    return active


def _fmt_revoked(channel_id, commits_revoked,
                 unnotified_commit=None, unnotified_revokes=None):

    unnotified_revokes = unnotified_revokes or []
    unnotified_secrets = [cr["revoke_secret"] for cr in unnotified_revokes]
    revoked = []
    for commit_revoked in commits_revoked:
        script = commit_revoked["script"]
        revoke_secret = commit_revoked["revoke_secret"]
        if unnotified_commit and unnotified_commit["script"] == script:
            continue  # drop revoke as client was not notified of commit
        payee_notified = 0 if revoke_secret in unnotified_secrets else 1
        data = {
            "channel_id": channel_id,
            "script": script,
            "revoke_secret": revoke_secret,
            "payee_notified": payee_notified
        }
        data.update(_script_data(script))
        revoked.append(data)
    return revoked


def save_channel_state(channel_id, state, unnotified_commit=None,
                       unnotified_revokes=None, cursor=None):
    cursor = cursor or get_cursor()

    # reformat state data
    commits_requested = _fmt_requested(channel_id, state["commits_requested"])
    commits_active = _fmt_active(channel_id, unnotified_commit,
                                 state["commits_active"])
    commits_revoked = _fmt_revoked(
        channel_id, state["commits_revoked"],
        unnotified_commit=unnotified_commit,
        unnotified_revokes=unnotified_revokes
    )

    # save state to db
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute(_RM_COMMITS, {"channel_id": channel_id})
    cursor.executemany(_ADD_COMMIT_REQUESTED, commits_requested)
    cursor.executemany(_ADD_COMMIT_ACTIVE, commits_active)
    cursor.executemany(_ADD_COMMIT_REVOKED, commits_revoked)
    cursor.execute("COMMIT;")


def send_payments_sum(handle, cursor=None):
    result = _one(_SEND_PAYMENTS_SUM, args={"handle": handle}, cursor=cursor)
    if result:
        return result["sum"]
    return 0


def recv_payments_sum(handle, cursor=None):
    result = _one(_RECV_PAYMENTS_SUM, args={"handle": handle}, cursor=cursor)
    if result:
        return result["sum"]
    return 0


def add_payment(payment, cursor=None):
    _exec(_ADD_PAYMENT, args=payment, cursor=cursor)


def key(pubkey, cursor=None):
    return _one(_KEY, args={"pubkey": pubkey}, cursor=cursor)


def channel_payer_key(channel_id, cursor=None):
    return _one(_CHANNEL_PAYER_KEY, args={"id": channel_id}, cursor=cursor)
