# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import apsw
from . import cfg


# old version -> migrate sql
MIGRATIONS = {
    0: open('picopayments/sql/migration_0.sql').read(),
}


def migrate(connection):
    cursor = connection.cursor()
    current_version = cursor.execute('PRAGMA user_version').fetchall()[0][0]
    while current_version in MIGRATIONS:
        cursor.execute(MIGRATIONS[current_version])
        current_version += 1
        cursor.execute('PRAGMA user_version = {0}'.format(current_version))


def get_connection():
    db_file = cfg.testnet_database if cfg.testnet else cfg.mainnet_database
    db_path = os.path.join(cfg.root, db_file)
    if not os.path.exists(os.path.dirname(db_path)):  # ensure root path exists
        os.makedirs(os.path.dirname(db_path))
    connection = apsw.Connection(db_path)
    migrate(connection)
    return connection


def get_fund_address(asset, connection=None):
    if connection is None:
        connection = get_connection()
    print("TODO implement get_fund_address")
    return None
