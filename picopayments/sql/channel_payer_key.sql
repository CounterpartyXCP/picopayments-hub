SELECT id, asset, pubkey, wif, address, unixtimestamp
FROM Keys INNER JOIN MicropaymentChannel 
ON MicropaymentChannel.payer_pubkey = Keys.pubkey
WHERE Keys.pubkey = :pubkey;
