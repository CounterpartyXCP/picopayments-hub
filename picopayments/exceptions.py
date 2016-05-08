# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


class IllegalStateError(Exception):

    def __init__(self, expected, got):
        msg = "Expected state '{0}' instead of '{1}'"
        super(IllegalStateError, self).__init__(msg.format(expected, got))


class InsufficientFunds(Exception):

    def __init__(self, needed, available):
        msg = "Needed funds '{0}', available '{1}'"
        super(InsufficientFunds, self).__init__(msg.format(needed, available))
