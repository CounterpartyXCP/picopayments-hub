SELECT 
    deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash,
    meta_complete, asset
FROM MicropaymentChannel INNER JOIN HubConnection 
ON MicropaymentChannel.id = HubConnection.recv_channel_id
WHERE HubConnection.handle = :handle;
