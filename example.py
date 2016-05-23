import time
import json
from picopayments.channel import Payer, Payee


PAYER_WIF = "cT9pEqELRn5v67hJmmmYQmPnsuezJeup7CqQiJBUTZnLLoxdydAb"
PAYEE_WIF = "cNXoRUC2eqcBEv1AmvPgM6NgCYV1ReTTHuAmVxaAh6AvVLHroSfU"
ASSET = "A14456548018133352000"
URL = "http://127.0.0.1:14000/api/"

payer = Payer(ASSET, api_url=URL, user="rpc", password="1234", testnet=True)
payee = Payee(ASSET, api_url=URL, user="rpc", password="1234", testnet=True)


# SETUP CHANNEL (DEPOSIT FUNDS)


# payee publishes pubkey and spend secret hash
payee_pubkey, spend_secret_hash = payee.setup(PAYEE_WIF)
print("Payee shares pubkey {0} and spend secret hash {1}".format(
    payee_pubkey, spend_secret_hash
))

# payer chooses deposit expire time and quantity
deposit_expire_time = 6 * 24 * 7  # one week with avg block gen speed
deposit_quantity = 1337  # in satoshi
print("Payer chooses deposit expire time {0} and quantity {1}.".format(
    deposit_expire_time, deposit_quantity
))

# payer makes deposit
deposit = payer.deposit(PAYER_WIF, payee_pubkey, spend_secret_hash,
                        deposit_expire_time, deposit_quantity)
print("Payer made deposit {0}".format(deposit))

# payer publishes deposit rawtx and script
payee.set_deposit(deposit["rawtx"], deposit["script"])
print("Payee received deposit from payer.")

# wait until deposit is confirmed
while not payer.is_deposit_confirmed():  # FIXME pass minconfirms
    time.sleep(1)
print("Deposit confirmed, channel now open.")

print("Channel transferred quantity {0}.".format(
    payee.get_transferred_amount()
))


# MOVE FUNDS BETWEEN PAYER TO PAYEE


# payer send funds to payee
for quantity in range(1, 10):

    # payee requests quantity and provides revoke secret hash for commit tx
    quantity, revoke_secret_hash = payee.request_commit(quantity)
    print("Payee requests quantity {0} with rovoke secret hash {1}.".format(
        quantity, revoke_secret_hash
    ))

    # payer creates and sign commit
    delay_time = 5
    commit = payer.create_commit(quantity, revoke_secret_hash, delay_time)
    print("Payer creates and shares commit {0}.".format(commit))

    # payer publishes commit and payee updates its state
    payee.set_commit(commit["rawtx"], commit["script"])
    print("Payee received commit.")

    print("Channel transferred quantity {0}.".format(
        payee.get_transferred_amount()
    ))

# payee returns funds by revealing revoke secrets
revoke_secrets = payee.revoke_until(4)
print("Payee returns funds by revealing revoke secrets {0}.".format(
    revoke_secrets
))

# payer receives revoke secrets and updates state
payer.revoke_all(revoke_secrets)
print("Payer received revoke secrets and updates state.")

print("Channel transferred quantity {0}.".format(
    payee.get_transferred_amount()
))


# CLOSE CHANNEL (PUBLISH COMMIT)


# payee closes channel by signing and publishing commit
txid = payee.close_channel()
print("Payee closes channel by publishing commit {0}.".format(txid))


print("Payer state:", json.dumps(payer.save(), indent=2))
print("Payee state:", json.dumps(payee.save(), indent=2))


payer.stop()
payee.stop()
