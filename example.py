import json
# import time
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


PAYER_WIF = "cSthi1Ye1sbHepC5s8rNukQBAKLCyct6hLg6MCH9Ybk1cKfGcPb2"
PAYEE_WIF = "cVmyYsHfeJWmCFy7N6DUeC4aXMS8vRR57aW7eGmpFVLfSHWjZ4jc"


payer = picopayments.channel.Payer(
    ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
)
payee = picopayments.channel.Payee(
    ASSET, api_url=API_URL, testnet=TESTNET, dryrun=DRYRUN
)


# payee published its pubkey and declares the spend secret hash
payee_pubkey, spend_secret_hash = payee.setup(PAYEE_WIF)

# payer deposits funds and choose expire time
deposit = payer.deposit(PAYER_WIF, payee_pubkey, spend_secret_hash,
                        picopayments.scripts.MAX_SEQUENCE, 1337)

# payer publishes deposit rawtx and script
deposit_rawtx = deposit["rawtx"]
deposit_script_hex = deposit["script"]
payee.set_deposit(deposit_rawtx, deposit_script_hex)

print(json.dumps(payer.save(), indent=2))
print(json.dumps(payee.save(), indent=2))

# # wait until deposit is confirmed
# while not payer.is_deposit_confirmed():
#     time.sleep(1)

# # payee requests amount and provides revoke secret hash for commit tx
# amount, revoke_secret_hash = payee.request_commit(1)

# # payer creates and sign commit
# commit_rawtx, commit_script = payer.create_commit(amount, revoke_secret_hash)

payer.stop()
payee.stop()
