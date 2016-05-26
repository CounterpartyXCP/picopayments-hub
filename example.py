import time
import json
from picopayments.channel import Payer, Payee


PAYER_WIF = "cQygpG38HiCDHsUCGn8QVKE8NFsgb9k1UHEwm8irEMuxMNX516QU"
PAYEE_WIF = "cS3ZxfC6sWMCv5hyQsA1Kjpy6Vqe9CQpfX5GEYevTDW4fXucw5uo"
ASSET = "A14456548018133352000"
URL = "http://127.0.0.1:14000/api/"

payer = Payer(ASSET, api_url=URL, user="rpc", password="1234", testnet=True)
payee = Payee(ASSET, api_url=URL, user="rpc", password="1234", testnet=True)


try:
    #################################
    # SETUP CHANNEL (DEPOSIT FUNDS) #
    #################################

    # payee publishes pubkey and spend secret hash
    payee_pubkey, spend_secret_hash = payee.setup(PAYEE_WIF)
    print("Payee shares pubkey {0} and spend secret hash {1}".format(
        payee_pubkey, spend_secret_hash
    ))

    # payer chooses deposit expire time and quantity
    deposit_expire_time = 6 * 24 * 7  # one week with std block gen speed
    deposit_quantity = 42  # in satoshi
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
    while not payer.is_deposit_confirmed(minconfirms=1):
        time.sleep(1)
    print("Deposit confirmed, channel now open.")

    print("Channel transferred quantity {0}.".format(
        payee.get_transferred_amount()
    ))

    ##################################
    # MOVE FUNDS FROM PAYER TO PAYEE #
    ##################################

    for quantity in range(1, 10):

        # payee requests quantity and provides revoke secret hash for commit tx
        quantity, revoke_secret_hash = payee.request_commit(quantity)
        print("Payee requests quantity {0} with rovoke secret hash {1}.".format(
            quantity, revoke_secret_hash
        ))

        # payer chooses delay time and creates, signs commit
        delay_time = 1  # block payee must wait to recover commied funds
        commit = payer.create_commit(quantity, revoke_secret_hash, delay_time)
        print("Payer creates and shares commit {0}.".format(commit))

        # payer publishes commit and payee updates its state
        payee.set_commit(commit["rawtx"], commit["script"])
        print("Payee received commit {0}.".format(commit))

        print("Channel transferred quantity {0}.".format(
            payee.get_transferred_amount()
        ))

    #######################
    # PAYEE RETURNS FUNDS #
    #######################

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

    ##################################
    # CLOSE CHANNEL (PUBLISH COMMIT) #
    ##################################

    # payee closes channel by signing and publishing commit
    txid = payee.close_channel()
    print("Payee closes channel by publishing commit {0}.".format(txid))

    # wait until payout confirmed
    while not payee.payout_confirmed(minconfirms=1):
        payee.update()  # payout recover if possible
        time.sleep(1)
    print("Payee payout recover transaction confirmed!")

    # wait until change confirmed
    while not payer.change_confirmed(minconfirms=1):
        payer.update()  # change recover if possible
        time.sleep(1)
    print("Payer change recover transaction confirmed!")

finally:
    print('"payer_state":', json.dumps(payer.save(), indent=2))
    print('"payee_state":', json.dumps(payee.save(), indent=2))


payer.stop()
payee.stop()
