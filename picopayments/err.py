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


class AssetDoesNotExist(Exception):

    def __init__(self, asset):
        msg = "Asset does not exist: '{0}'"
        super(AssetDoesNotExist, self).__init__(msg.format(asset))


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


class AssetMissmatch(Exception):

    def __init__(self, expected, found):
        msg = "Expected asset {0} does not match found asset {1}!"
        super(AssetMissmatch, self).__init__(msg.format(expected, found))


class AuthPubkeyMissmatch(Exception):

    def __init__(self, expected, found):
        msg = "Given pubkey {0} does not match signing pubkey {1}!".format(
            found, expected
        )
        super(AuthPubkeyMissmatch, self).__init__(msg)


class ClientPubkeyMissmatch(Exception):

    def __init__(self, expected, found):
        msg = "Given pubkey {0} does not match channel client pubkey {1}!"
        super(ClientPubkeyMissmatch, self).__init__(
            msg.format(found, expected)
        )


class InvalidSignature(Exception):

    def __init__(self, pubkey, signature, data):
        msg = "Invalid signature for pubkey {0}, signature {1}, data {2}"
        super(InvalidSignature, self).__init__(
            msg.format(pubkey, signature, data)
        )


class DepositExpired(Exception):

    def __init__(self, handle, side):
        msg = "Deposit expired for connection {0} side {1}"
        super(DepositExpired, self).__init__(msg.format(handle, side))


class InsufficientFunds(Exception):

    def __init__(self, asset, quantity):
        msg = "No keypair for {0} with {1} funds."
        super(InsufficientFunds, self).__init__(msg.format(asset, quantity))
