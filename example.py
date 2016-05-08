# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from picopayments.control import Control

asset = "A14456548018133352000"
control = Control(
    asset, user="rpc", password="1234", api_url="http://127.0.0.1:14000/api/",
    testnet=True, dryrun=True
)
wif = "cTvCnpvQJE3TvNejkWbnFA1z6jLJjB2xXXapFabGsazCz2QNYFQb"
src_address = "n2WQGAvnDS1vf7uXToLou6kLxJXRGFHo2b"


# info = {
#   "txid": "e882d2207a642f9615d0539fd11db5ed6500bc16f4a43f17580e4a216ba9691d",
#   "quantity": 31337,
#   "script": (
#       "OP_IF OP_2 035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd94dab"
#       "7c7513b56 027690887ac2455b6b19c5f4268a8a9c09228351368b9a7643ad791282"
#       "c3148759 OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 ab701c76f0cb"
#       "3d3d30c7ef832c3a7f3e96d2a2d5 OP_EQUALVERIFY 035f57228dc3b9a3224f2d48"
#       "a1e2f9886f8412a0e77afdec28fd94dab7c7513b56 OP_CHECKSIG OP_ELSE OP_5 "
#       "OP_NOP3 OP_DROP 035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd"
#       "94dab7c7513b56 OP_CHECKSIG OP_ENDIF OP_ENDIF"
#   ),
#   "rawtx": (
#       "01000000016a6ee3779540bea4d26dacc8c1c66c3f5dcc78d462cdddccea9606db18"
#       "68a1de020000006b483045022100d919da518f797241a1637e2db8569b9b0e6c66f0"
#       "2f29afa2985477085f2a95f902204dbf65d7524f8f18e9bf14cd86353fbca4bdae85"
#       "9833284e5947f1268550c5fd0121035f57228dc3b9a3224f2d48a1e2f9886f8412a0"
#       "e77afdec28fd94dab7c7513b56ffffffff03d2b400000000000017a914599e01f23b"
#       "b03f45dc970a02ee2c1a3e6a6072378700000000000000001e6a1ce482326311df38"
#       "51dc224bd993c0d409cf6fe658d2e68dbc55c4a279f8d98f3e000000001976a914e6"
#       "3fe6f12b3300f2fad00a1270b71529985d972d88ac00000000"
#   ),
#   "asset": "A14456548018133352000",
#   "address": "2N1R5QvAsVEFGkrsAonuZDBPfrLnfKJ8Uqo"
# }
# info = {
#   "asset": "A14456548018133352000",
#   "script": (
#       "OP_IF OP_2 035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd94dab"
#       "7c7513b56 027690887ac2455b6b19c5f4268a8a9c09228351368b9a7643ad791282"
#       "c3148759 OP_2 OP_CHECKMULTISIG OP_ELSE OP_IF OP_HASH160 c3b1f6dc2f98"
#       "689cb010420eb0165f6a2155b6e4 OP_EQUALVERIFY 035f57228dc3b9a3224f2d48"
#       "a1e2f9886f8412a0e77afdec28fd94dab7c7513b56 OP_CHECKSIG OP_ELSE OP_5 "
#       "OP_NOP3 OP_DROP 035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd"
#       "94dab7c7513b56 OP_CHECKSIG OP_ENDIF OP_ENDIF"
#   ),
#   "address": "2NF38gQAeejopENShQ56tD69aYYjE6QzkcV",
#   "rawtx": (
#       "01000000011d69a96b214a0e58173fa4f416bc0065edb51dd19f53d015962f647a20"
#       "d282e8020000006b483045022100c1fb3ae9e6ee72c24ebe6814bb4551ffc129ac50"
#       "8ad78805e7f818ce364f563a022018bb0ca552f8077d20f86c886e82da41a4da88b6"
#       "83791addc875fd080061d50c0121035f57228dc3b9a3224f2d48a1e2f9886f8412a0"
#       "e77afdec28fd94dab7c7513b56ffffffff03d2b400000000000017a914ef095832a2"
#       "6d622f6119e9223ac2fc1887d2ca0e8700000000000000001e6a1ca6e2e8d7d8caa6"
#       "42e33c7421fa59b142260745fd5dc598b386ef50b016fe8e3e000000001976a914e6"
#       "3fe6f12b3300f2fad00a1270b71529985d972d88ac00000000"
#   ),
#   "txid": "9869e51352ab868324a2663c96eeffefccb0d36af8b3e184344fabacea8d4ded",
#   "quantity": 31337
# }
# rawtx = control.recover(wif, info["rawtx"], info["script"])

key = control.btctxstore.create_key()
dest_address = control.btctxstore.get_address(key)
print("{0} -> {1}".format(key, dest_address))
unsigned = control.create_tx(src_address, dest_address, 1337, 200000)
print(unsigned)
signed = control.btctxstore.sign_tx(unsigned, wifs=[wif])
print(signed)


# WIF = "cPZmtXNUPwdsAjbowvAGEKLCqgQ38ZUu1DhFuQoeJoRdH6XWUwNX"
# address:  mhNk2YmEkYNi8PVY86dPRr8z93CWQzXyAs
# A14456548018133352000: 1337
# BTC: 100000
