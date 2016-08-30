# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import apsw
from threading import RLock
from counterpartylib.lib.micropayments import util
from counterpartylib.lib.micropayments import scripts
from picopayments import etc
from picopayments import sql
from picopayments.sql import load
from picopayments.sql import make_fetchone
from picopayments.sql import make_fetchall
from picopayments.sql import make_execute


# old version -> migrate sql
_MIGRATIONS = {
    0: load("migration_0"),
}
_HANDLE_EXISTS = "SELECT EXISTS(SELECT * FROM HubConnection WHERE handle = ?);"
_COMMITS_REQUESTED = load("commits_requested")
_COMMITS_ACTIVE = load("commits_active")
_COMMITS_REVOKED = load("commits_revoked")
_ADD_HUB_CONNECTION = load("add_hub_connection")
_ADD_REVOKE_SECRET = load("add_revoke_secret")
_ADD_KEY = load("add_key")
_ADD_COMMIT_REQUESTED = load("add_commit_requested")
_ADD_COMMIT_ACTIVE = load("add_commit_active")
_ADD_COMMIT_REVOKED = load("add_commit_revoked")
_RM_COMMITS = load("rm_commits")
_COMPLETE_HUB_CHANNELS = load("complete_hub_channels")
_SET_PAYMENT_NOTIFIED = load("set_payment_notified")
_SET_REVOKE_NOTIFIED = load("set_revoke_notified")
_SET_NEXT_REVOKE_SECRET_HASH = load("set_next_revoke_secret_hash")


key = make_fetchone("key")
terms = make_fetchone("terms")
channel_payer_key = make_fetchone("channel_payer_key")
receive_channel = make_fetchone("receive_channel")
unnotified_commit = make_fetchone("unnotified_commit")
hub_connections = make_fetchall("hub_connections")
set_commit_notified = make_execute("set_commit_notified")
unnotified_revokes = make_fetchall("unnotified_revokes")
add_payment = make_execute("add_payment")
unnotified_payments = make_fetchall("unnotified_payments")
hub_connection = make_fetchone("hub_connection")
micropayment_channel = make_fetchone("micropayment_channel")
hub2client_payments_sum = make_fetchone("hub2client_payments_sum", getsum=True)
client2hub_payments_sum = make_fetchone("client2hub_payments_sum", getsum=True)


lock = RLock()  # FIXME move to etc


def setup():

    # get connection
    connection = apsw.Connection(etc.path_database)

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
    sql.execute(_SET_NEXT_REVOKE_SECRET_HASH, data, cursor=cursor)
    sql.execute(_COMPLETE_HUB_CHANNELS, data, cursor=cursor)
    add_revoke_secret_args = {
        "secret_hash": data["secret_hash"],
        "secret_value": data["secret_value"],
        "channel_id": data["client2hub_channel_id"],
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
    delay_time = scripts.get_commit_delay_time(util.h2b(script))
    secret_hash = scripts.get_commit_revoke_secret_hash(util.h2b(script))
    commit_address = util.script2address(util.h2b(script),
                                         netcode=etc.netcode)
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
    cursor = cursor or sql.get_cursor()

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


def set_next_revoke_secret_hash(handle, next_revoke_secret_hash, cursor=None):
    args = {
        "handle": handle, "next_revoke_secret_hash": next_revoke_secret_hash
    }
    sql.execute(_SET_NEXT_REVOKE_SECRET_HASH, args, cursor=cursor)
