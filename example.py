import json
import picopayments


ASSET = "A14456548018133352000"
USER = "rpc"
PASSWORD = "1234"
API_URL = "http://127.0.0.1:14000/api/"
TESTNET = True
DRYRUN = True


WIF = "cQcyHaFZpQvo7BRcgtEoHPP2CC7gLbBqvZk6HRL7xXdyoh4FeDGi"
SPEND_SECRET = (
    "89a4a2395b242fcf77c766fc47dc6c14399c06a197f2322c8c503da87e76d842"
)
SPEND_SECRET_HASH = picopayments.util.hash160hex(SPEND_SECRET)
QUANTITY = 1337
PAYEE_PUBKEY = (
    "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8"
)


# channel.deposit(WIF, PAYEE_PUBKEY, SPEND_SECRET_HASH,
#                 picopayments.scripts.MAX_SEQUENCE, 1337)
channel = picopayments.channel.Payer(ASSET, api_url=API_URL,
                                     testnet=TESTNET, dryrun=DRYRUN)
channel.load({
  "payer_wif": "cQcyHaFZpQvo7BRcgtEoHPP2CC7gLbBqvZk6HRL7xXdyoh4FeDGi",
  "deposit_script_hex": "63522103129f39ffddfea5d17bca8e98a1856a5b37adc40c8905fffbe4a38e5896221657210327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f852ae6763a914c1fc72735bfeac8686cbc9e81195d7241c00e813882103129f39ffddfea5d17bca8e98a1856a5b37adc40c8905fffbe4a38e5896221657ac6703ffff00b2752103129f39ffddfea5d17bca8e98a1856a5b37adc40c8905fffbe4a38e5896221657ac6868",
  "spend_secret": None,
  "deposit_rawtx": "01000000013ba248c5fd88e39206fe49377a7ce3d1bbace739d230cd1482bcf957959c8487000000006b483045022100eee8680624e8ece63b4944f9295c0d858783800b1fc662e1c556b1936e1dfe620220299aca5e1c0bc344a195d648577cc8f423e689b38e1ed00ec50530c14d8eafce012103129f39ffddfea5d17bca8e98a1856a5b37adc40c8905fffbe4a38e5896221657ffffffff03d2b400000000000017a9144b09aa0dcb5a25483078b0e37a954f5495ac12528700000000000000001e6a1cc9d0c883c54aeb6b242a5a5b4ea745fb0d00b8e9f1024693d6fccbda5e310200000000001976a914d0feaad51146bd27a8707368729a9ae7d00ab58a88ac00000000",
  "timeout_rawtx": None,
  "payee_wif": None,
  "payee_pubkey": "0327f017c35a46b759536309e6de256ad44ad609c1c4aed0e2cdb82f62490f75f8",
  "change_rawtx": None,
  "payer_pubkey": "03129f39ffddfea5d17bca8e98a1856a5b37adc40c8905fffbe4a38e5896221657"
})
channel.set_spend_secret(SPEND_SECRET)
channel.update()
print(json.dumps(channel.save(), indent=2))
