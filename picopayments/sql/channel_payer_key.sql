SELECT 
    Keys.id AS 'id', 
    asset, 
    pubkey, 
    wif, 
    address, 
    Keys.unixtimestamp AS 'unixtimestamp'
FROM Keys INNER JOIN MicropaymentChannel 
ON MicropaymentChannel.payer_pubkey = Keys.pubkey
WHERE MicropaymentChannel.id = :id;
