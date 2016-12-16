# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import pkg_resources
from picopayments_hub import etc


def _row_to_dict_factory(cursor, row):
    return {k[0]: row[i] for i, k in enumerate(cursor.getdescription())}


def get_cursor():
    return etc.database_connection.cursor()


def load(script_name):
    sql_path = os.path.join("sql", "{0}.sql".format(script_name))
    script = pkg_resources.resource_stream("picopayments_hub", sql_path).read()
    return script.decode("utf-8")


def execute(script, args=None, cursor=None):
    """Execute script"""
    cursor = cursor or get_cursor()
    cursor.execute(script, args)


def make_execute(script_name):
    script = load(script_name)

    def func(**kwargs):
        cursor = kwargs.pop("cursor", None)
        return execute(script, args=kwargs, cursor=cursor)
    return func


def fetchone(script, args=None, cursor=None, getsum=False):
    """Execute script and fetch one row."""
    cursor = cursor or get_cursor()
    cursor.setrowtrace(_row_to_dict_factory)
    result = cursor.execute(script, args).fetchone()
    if getsum:
        return result["sum"] if result else 0
    return result


def make_fetchone(script_name, getsum=False):
    script = load(script_name)

    def func(**kwargs):
        cursor = kwargs.pop("cursor", None)
        return fetchone(script, args=kwargs, cursor=cursor, getsum=getsum)
    return func


def fetchall(script, args=None, cursor=None):
    """Execute script and fetch all rows."""
    cursor = cursor or get_cursor()
    cursor.setrowtrace(_row_to_dict_factory)
    return cursor.execute(script, args).fetchall()


def make_fetchall(script_name):
    script = load(script_name)

    def func(**kwargs):
        cursor = kwargs.pop("cursor", None)
        return fetchall(script, args=kwargs, cursor=cursor)
    return func
