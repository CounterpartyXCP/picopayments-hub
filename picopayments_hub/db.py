# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import apsw
from micropayment_core import util
from micropayment_core import scripts
from picopayments_hub import etc
from picopayments_hub import sql


# old version -> migrate sql
_MIGRATIONS = {
    0: sql.load("migration_0"),
    1: sql.load("migration_1"),
    2: sql.load("migration_2"),
    3: sql.load("migration_3"),
}
_HANDLE_EXISTS = "SELECT EXISTS(SELECT * FROM HubConnection WHERE handle = ?);"
_COMMITS_REQUESTED = sql.load("commits_requested")
_COMMITS_ACTIVE = sql.load("commits_active")
_COMMITS_REVOKED = sql.load("commits_revoked")
_ADD_HUB_CONNECTION = sql.load("add_hub_connection")
_ADD_REVOKE_SECRET = sql.load("add_revoke_secret")
_ADD_KEY = sql.load("add_key")
_ADD_COMMIT_REQUESTED = sql.load("add_commit_requested")
_ADD_COMMIT_ACTIVE = sql.load("add_commit_active")
_ADD_COMMIT_REVOKED = sql.load("add_commit_revoked")
_RM_COMMITS = sql.load("rm_commits")
_COMPLETE_CONNECTION = sql.load("complete_connection")
_SET_PAYMENT_NOTIFIED = sql.load("set_payment_notified")
_SET_REVOKE_NOTIFIED = sql.load("set_revoke_notified")


key = sql.make_fetchone("key")
get_secret = sql.make_fetchone("get_secret")
add_secret = sql.make_execute("add_secret")
keys = sql.make_fetchall("keys")
terms = sql.make_fetchone("terms")
channel_payer_key = sql.make_fetchone("channel_payer_key")
c2h_channel = sql.make_fetchone("c2h_channel")
h2c_channel = sql.make_fetchone("h2c_channel")
unnotified_commit = sql.make_fetchone("unnotified_commit")

hub_connections_complete = sql.make_fetchall("hub_connections_complete")
hub_connections_open = sql.make_fetchall("hub_connections_open")
hub_connections_closed = sql.make_fetchall("hub_connections_closed")
hub_connections_all = sql.make_fetchall("hub_connections_all")
hub_connections_recoverable = sql.make_fetchall("hub_connections_recoverable")

hub_connection = sql.make_fetchone("hub_connection")
set_commit_notified = sql.make_execute("set_commit_notified")
set_connection_closed = sql.make_execute("set_connection_closed")
set_next_revoke_secret_hash = sql.make_execute("set_next_revoke_secret_hash")
get_next_revoke_secret_hash = sql.make_fetchone("get_next_revoke_secret_hash")
unnotified_revokes = sql.make_fetchall("unnotified_revokes")
add_payment = sql.make_execute("add_payment")
unnotified_payments = sql.make_fetchall("unnotified_payments")
micropayment_channel = sql.make_fetchone("micropayment_channel")
recv_payments_sum = sql.make_fetchone("recv_payments_sum", True)
send_payments_sum = sql.make_fetchone("send_payments_sum", True)


def setup():

    # get connection
    connection = apsw.Connection(etc.database_path)

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
    etc.database_connection = connection

    # migrate
    script = "PRAGMA user_version;"
    db_version = sql.fetchone(script, cursor=cursor)["user_version"]
    while db_version in _MIGRATIONS:
        sql.execute(_MIGRATIONS[db_version], cursor=cursor)
        db_version += 1
        script = "PRAGMA user_version = {0};".format(db_version)
        sql.execute(script, cursor=cursor)


def add_keys(keys, cursor=None):
    cursor = cursor or sql.get_cursor()
    cursor.execute("BEGIN TRANSACTION")
    cursor.executemany(_ADD_KEY, keys)
    cursor.execute("COMMIT")


def commits_requested(channel_id, cursor=None):
    args = {"channel_id": channel_id}
    entries = sql.fetchall(_COMMITS_REQUESTED, args=args, cursor=cursor)
    return [entry["revoke_secret_hash"] for entry in entries]


def commits_active(channel_id, cursor=None):
    args = {"channel_id": channel_id}
    entries = sql.fetchall(_COMMITS_ACTIVE, args=args, cursor=cursor)
    return [{"rawtx": e["rawtx"], "script": e["script"]} for e in entries]


def commits_revoked(channel_id, cursor=None):
    args = {"channel_id": channel_id}
    entries = sql.fetchall(_COMMITS_REVOKED, args=args, cursor=cursor)
    return [
        {"script": e["script"], "revoke_secret": e["revoke_secret"]}
        for e in entries
    ]


def add_hub_connection(data, cursor=None):
    cursor = cursor or sql.get_cursor()
    cursor.execute("BEGIN TRANSACTION")
    sql.execute(_ADD_HUB_CONNECTION, data, cursor=cursor)
    cursor.execute("COMMIT")


def complete_hub_connection(data, cursor=None):
    cursor = cursor or sql.get_cursor()
    cursor.execute("BEGIN TRANSACTION")
    set_next_revoke_secret_hash(
        handle=data["handle"],
        next_revoke_secret_hash=data["next_revoke_secret_hash"],
        cursor=cursor
    )
    sql.execute(_COMPLETE_CONNECTION, data, cursor=cursor)
    add_revoke_secret_args = {
        "secret_hash": data["secret_hash"],
        "secret_value": data["secret_value"],
        "channel_id": data["c2h_channel_id"],
    }
    sql.execute(_ADD_REVOKE_SECRET, args=add_revoke_secret_args, cursor=cursor)
    cursor.execute("COMMIT")


def handles_exist(handles, cursor=None):
    args = [(handle,) for handle in handles]
    cursor = cursor or sql.get_cursor()
    result = cursor.executemany(_HANDLE_EXISTS, args).fetchall()
    return all([r[0] for r in result])


def set_payments_notified(payment_ids, cursor=None):
    cursor = cursor or sql.get_cursor()
    cursor.executemany(_SET_PAYMENT_NOTIFIED, payment_ids)


def set_revokes_notified(revoke_ids, cursor=None):
    cursor = cursor or sql.get_cursor()
    cursor.executemany(_SET_REVOKE_NOTIFIED, revoke_ids)


def add_revoke_secret(channel_id, secret_hash, secret_value, cursor=None):
    args = {
        "channel_id": channel_id,
        "secret_hash": secret_hash,
        "secret_value": secret_value
    }
    sql.execute(_ADD_REVOKE_SECRET, args=args, cursor=cursor)


def load_channel_state(channel_id, asset, cursor=None):
    channel = micropayment_channel(id=channel_id, cursor=cursor)
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
    delay_time = scripts.get_commit_delay_time(script)
    secret_hash = scripts.get_commit_revoke_secret_hash(script)
    commit_address = util.script_address(script, netcode=etc.netcode)
    return {
        "commit_address": commit_address,
        "delay_time": delay_time,
        "revoke_secret_hash": secret_hash,
    }


def _fmt_active(channel_id, h2c_unnotified_commit, commits_active):
    active = []
    for commit_active in commits_active:
        script = commit_active["script"]
        rawtx = commit_active["rawtx"]

        payee_notified = 1
        if h2c_unnotified_commit and h2c_unnotified_commit["script"] == script:
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
                 h2c_unnotified_commit=None, unnotified_revoke_secrets=None):

    unnotified_revoke_secrets = unnotified_revoke_secrets or []
    revoked = []
    for commit_revoked in commits_revoked:
        script = commit_revoked["script"]
        revoke_secret = commit_revoked["revoke_secret"]
        if h2c_unnotified_commit and h2c_unnotified_commit["script"] == script:
            continue  # drop revoke as client was not notified of commit
        payee_notified = 0 if revoke_secret in unnotified_revoke_secrets else 1
        data = {
            "channel_id": channel_id,
            "script": script,
            "revoke_secret": revoke_secret,
            "payee_notified": payee_notified
        }
        data.update(_script_data(script))
        revoked.append(data)
    return revoked


def save_channel_state(channel_id, state, h2c_unnotified_commit=None,
                       unnotified_revoke_secrets=None, cursor=None):

    cursor = cursor or sql.get_cursor()

    # reformat state data
    commits_requested = _fmt_requested(channel_id, state["commits_requested"])
    commits_active = _fmt_active(channel_id, h2c_unnotified_commit,
                                 state["commits_active"])
    commits_revoked = _fmt_revoked(
        channel_id, state["commits_revoked"],
        h2c_unnotified_commit=h2c_unnotified_commit,
        unnotified_revoke_secrets=unnotified_revoke_secrets
    )

    # save state to db
    cursor.execute(_RM_COMMITS, {"channel_id": channel_id})
    cursor.executemany(_ADD_COMMIT_REQUESTED, commits_requested)
    cursor.executemany(_ADD_COMMIT_ACTIVE, commits_active)
    cursor.executemany(_ADD_COMMIT_REVOKED, commits_revoked)
