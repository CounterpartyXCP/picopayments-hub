# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


class ChannelAlreadyUsed(Exception):

    def __init__(self, channel_address, transactions):
        msg = "Channel '{0}' already used: '{1}'"
        super(ChannelAlreadyUsed, self).__init__(msg.format(
            channel_address, transactions
        ))


class InsufficientFunds(Exception):

    def __init__(self, needed, available):
        msg = "Needed funds '{0}', available '{1}'"
        super(InsufficientFunds, self).__init__(msg.format(needed, available))
