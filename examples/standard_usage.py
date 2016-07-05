# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import os
import time
import json
import picopayments


# url = "http://45.55.201.116:14000/api/"  # storj counterpartylib server
url = "http://127.0.0.1:14000/api/"


asset = "A14456548018133352000"
api = picopayments.Api(url=url, testnet=True)


# setup alice (payer)
alice_wif = "cQDSZQdKiAcMNdMZu1fPSmGsjxpqcW53BNd9mRt2UJxchYAHN6iR"
alice_pubkey = picopayments.util.wif2pubkey(alice_wif)
alice_state = None


# setup bob (payee)
bob_wif = "cRWyuBAtE1CLzpGh3xjcXu9KshBRYXiFNZFoewuM4K3HEXxRJh3n"
bob_pubkey = picopayments.util.wif2pubkey(bob_wif)
bob_state = None
bob_revoke_secrets = {}  # hash -> secret
spend_secret = picopayments.util.b2h(os.urandom(32))


# bob shares spend secret hash and pubkey with alice
spend_secret_hash = picopayments.util.hash160hex(spend_secret)
print("Bob shares his pubkey {0} and the spend secret hash {1}".format(
    bob_pubkey, spend_secret_hash
))


# alice creates deposit tx and initial state
result = api.call(
    method="mpc_make_deposit",
    params={
        "asset": asset,
        "payer_pubkey": alice_pubkey,
        "payee_pubkey": bob_pubkey,
        "spend_secret_hash": spend_secret_hash,
        "expire_time": 1337,  # in blocks
        "quantity": 42  # in satoshis
    }
)
alice_state = result["state"]  # get initial state for alice


# alice shares the deposit_script with bob
deposit_script = result["deposit_script"]
deposit_address = picopayments.util.scripthex2address(
    deposit_script, netcode="XTN"
)
print("Alice shares the deposit script {0} with the address {1}".format(
    deposit_script, deposit_address
))


# alice signes and publishes deposit tx
unsigned_deposit_rawtx = result["topublish"]
signed_deposit_rawtx = picopayments.scripts.sign_deposit(
    api.btctxstore, alice_wif, unsigned_deposit_rawtx
)
deposit_txid = api.call(
    method="sendrawtransaction",
    params={"tx_hex": signed_deposit_rawtx}
)
print("Alice published the deposit tx {0}".format(deposit_txid))


# bob creates initial state and verifies the deposit script
bob_state = api.call(
    method="mpc_set_deposit",
    params={
        "asset": asset,
        "deposit_script": deposit_script,
        "expected_payee_pubkey": bob_pubkey,
        "expected_spend_secret_hash": spend_secret_hash
    }
)


print("Waiting until deposit confirmed ...")
while not api.btctxstore.confirms(deposit_txid):
    time.sleep(10)


# incrementally move funds from alice to bob
for quantity in range(1, 42):

    # payee chooses and remembers a revoke secret for the requested commit
    revoke_secret = picopayments.util.b2h(os.urandom(32))
    revoke_secret_hash = picopayments.util.hash160hex(revoke_secret)
    bob_revoke_secrets[revoke_secret_hash] = revoke_secret

    # payee add revoke secret to own state and validate requested quantity
    result = api.call(
        method="mpc_request_commit",
        params={
            "state": bob_state,
            "quantity": quantity,
            "revoke_secret_hash": revoke_secret_hash,
        }
    )
    bob_state = result["state"]

    # payee shared requested quantity and revoke secret hash

    # payer choose a delay time and creates requested commit
    result = api.call(
        method="mpc_create_commit",
        params={
            "state": alice_state,
            "quantity": result["quantity"],
            "revoke_secret_hash": result["revoke_secret_hash"],
            "delay_time": 1,
        }
    )
    alice_state = result["state"]
    unsigned_commit_rawtx = result["tosign"]["commit_rawtx"]
    deposit_script = result["tosign"]["deposit_script"]

    # payer signs and shares the created commit
    half_signed_commit_rawtx = picopayments.scripts.sign_created_commit(
        api.btctxstore, alice_wif, unsigned_commit_rawtx, deposit_script
    )
    commit_script = result["commit_script"]

    # payee adds commit to its state
    bob_state = api.call(
        method="mpc_add_commit",
        params={
            "state": bob_state,
            "commit_rawtx": half_signed_commit_rawtx,
            "commit_script": commit_script
        }
    )

# payee gets revoke secret hashes that need to be shared to reverse channel
secret_hashes = api.call(
    method="mpc_revoke_secret_hashes_above",
    params={
        "state": bob_state,
        "quantity": 4
    }
)

# payee reverses channel by sharing revoke secrets
revoke_secrets = [bob_revoke_secrets[sh] for sh in secret_hashes]

# payee revokes commits
bob_state = api.call(
    method="mpc_revoke_all",
    params={
        "state": bob_state,
        "secrets": revoke_secrets
    }
)

# payer revokes commits
alice_state = api.call(
    method="mpc_revoke_all",
    params={"state": alice_state, "secrets": revoke_secrets}
)

# Transferred amount
print("Alice quantity transferred: {0}".format(api.call(
    method="mpc_transferred_amount",
    params={"state": alice_state}
)))
print("Bob quantity transferred: {0}".format(api.call(
    method="mpc_transferred_amount",
    params={"state": bob_state}
)))

# payee gets top commit for closing the channel
result = api.call(method="mpc_highest_commit", params={"state": bob_state})
half_signed_commit_rawtx = result["commit_rawtx"]
deposit_script = result["deposit_script"]

# close channel by signing and publishing the top commit
fully_signed_commit_rawtx = picopayments.scripts.sign_finalize_commit(
    api.btctxstore, bob_wif, half_signed_commit_rawtx, deposit_script
)
published_commit_txid = api.call(
    method="sendrawtransaction",
    params={"tx_hex": fully_signed_commit_rawtx}
)
print("Bob closes channel by publishing commit tx {0}".format(
    published_commit_txid
))

# TODO get deposit change amount
# TODO get amount commited

# wait until required delay passes and get payout transactions
print("Waiting until required delay passes and get payout transactions")
payouts = None
while not payouts:
    payouts = api.call(method="mpc_payouts", params={"state": bob_state})
    time.sleep(10)

# get transferred by creating/publishing the payout transaction
print("PAYOUTS", json.dumps(payouts, indent=2))
for payout in payouts:
    commit_script = payout["commit_script"]
    unsigned_payout_rawtx = payout["payout_rawtx"]
    signed_payout_rawtx = picopayments.scripts.sign_payout_recover(
        api.btctxstore, bob_wif, unsigned_payout_rawtx,
        commit_script, spend_secret
    )
    published_payout_txid = api.call(
        method="sendrawtransaction",
        params={"tx_hex": signed_payout_rawtx}
    )
    print("Published payout transaction {0}".format(published_payout_txid))

recoverables = {}
while not recoverables.get("change"):
    recoverables = api.call("mpc_recoverables", {"state": alice_state})
    time.sleep(10)

# get change by creating/publishing the change transaction
print("RECOVERABLES", json.dumps(recoverables, indent=2))
for change_recoverable in recoverables["change"]:
    unsigned_change_rawtx = change_recoverable["change_rawtx"]
    deposit_script = change_recoverable["deposit_script"]
    spend_secret = change_recoverable["spend_secret"]
    signed_change_rawtx = picopayments.scripts.sign_change_recover(
        api.btctxstore, alice_wif, unsigned_change_rawtx,
        deposit_script, spend_secret
    )
    published_change_txid = api.call(
        method="sendrawtransaction",
        params={"tx_hex": signed_change_rawtx}
    )
    print("Published change transaction {0}".format(published_change_txid))
