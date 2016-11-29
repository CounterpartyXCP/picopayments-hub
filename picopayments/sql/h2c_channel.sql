SELECT 
    deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash, asset
FROM MicropaymentChannel INNER JOIN HubConnection 
ON MicropaymentChannel.id = HubConnection.h2c_channel_id
WHERE HubConnection.handle = :handle;
