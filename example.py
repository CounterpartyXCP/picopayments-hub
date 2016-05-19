import time
import json
from picopayments.channel import Payer, Payee


PAYER_WIF = "cSEAvYo5yDPzuBCZcttaxBpH4UpxYCPtaZSy8iRXxDG4J9snisJZ"
PAYEE_WIF = "cNjNTW74gPNat6Svc7hdpxr3P1zSMNhC2vAhCLk5546dW2w3hZFc"
ASSET = "A14456548018133352000"
URL = "http://127.0.0.1:14000/api/"

payer = Payer(ASSET, api_url=URL, user="rpc", password="1234", testnet=True)
payee = Payee(ASSET, api_url=URL, user="rpc", password="1234", testnet=True)


# SETUP CHANNEL (DEPOSIT FUNDS)


# payee publishes pubkey and spend secret hash
payee_pubkey, spend_secret_hash = payee.setup(PAYEE_WIF)

# payer chooses an expire time and deposits funds
deposit_expire_time = 6 * 24 * 7  # one week with avg block gen speed
deposit_quantity = 1337  # in satoshi
deposit = payer.deposit(PAYER_WIF, payee_pubkey, spend_secret_hash,
                        deposit_expire_time, deposit_quantity)

# payer publishes deposit rawtx and script
payee.set_deposit(deposit["rawtx"], deposit["script"])


print(json.dumps(payer.save(), indent=2))
print(json.dumps(payee.save(), indent=2))


# wait until deposit is confirmed
while not payer.is_deposit_confirmed():  # FIXME pass minconfirms
    time.sleep(1)


# MOVE FUNDS BETWEEN PAYER TO PAYEE


# payer send funds to payee
for quantity in range(1, 10):

    # payee requests quantity and provides revoke secret hash for commit tx
    quantity, revoke_secret_hash = payee.request_commit(quantity)

    # payer creates and sign commit
    delay_time = 5
    commit = payer.create_commit(quantity, revoke_secret_hash, delay_time)

    # payer publishes commit and payee updates its state
    payee.set_commit(commit["rawtx"], commit["script"])


# payee returns funds by revealing revoke secrets
revoke_secrets = payee.revoke_until(4)
payer.revoke_all(revoke_secrets)


# CLOSE CHANNEL (PUBLISH COMMIT)

# payee signs and publishes commit
txid = payee.close_channel()


print(json.dumps(payer.save(), indent=2))
print(json.dumps(payee.save(), indent=2))


payer.stop()
payee.stop()
