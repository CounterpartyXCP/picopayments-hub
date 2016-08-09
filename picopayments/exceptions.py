# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


class InvalidUrl(Exception):

    def __init__(self, url):
        msg = "Invalid url: '{0}'"
        super(InvalidUrl, self).__init__(msg.format(url))


class AssetNotInTerms(Exception):

    def __init__(self, asset):
        msg = "No terms for given asset: '{0}'"
        super(AssetNotInTerms, self).__init__(msg.format(asset))


class DepositAlreadyGiven(Exception):

    def __init__(self, handle):
        msg = "Deposit script already given for handle: '{0}'"
        super(DepositAlreadyGiven, self).__init__(msg.format(handle))


class HandleNotFound(Exception):

    def __init__(self, handle):
        msg = "No hub connection for given handle: '{0}'"
        super(HandleNotFound, self).__init__(msg.format(handle))


class HandlesNotFound(Exception):

    def __init__(self, handles):
        msg = "One or more unknown handles: {0}"
        super(HandlesNotFound, self).__init__(msg.format(repr(handles)))


class RpcCallFailed(Exception):

    def __init__(self, payload, response):
        msg = "Rpc call failed! {0} -> {1}".format(payload, response)
        super(RpcCallFailed, self).__init__(msg)


class PaymentExceedsSpendable(Exception):

    def __init__(self, amount, spendable, token):
        msg = "Payment amount exceeds payer spendable! {0}: {1} > {2}".format(
            token, amount, spendable
        )
        super(PaymentExceedsSpendable, self).__init__(msg)


class PaymentExceedsReceivable(Exception):

    def __init__(self, amount, spendable, token):
        msg = "Payment amount exceeds payee receivable! {0}: {1} > {2}".format(
            token, amount, spendable
        )
        super(PaymentExceedsReceivable, self).__init__(msg)
