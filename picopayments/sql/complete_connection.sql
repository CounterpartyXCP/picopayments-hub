-- update send channel
UPDATE MicropaymentChannel SET
    deposit_script = :hub2client_deposit_script,
    deposit_address = :hub2client_deposit_address,
    expire_time = :expire_time
WHERE
    id = :hub2client_channel_id;

-- update receive channel
UPDATE MicropaymentChannel SET
    deposit_script = :client2hub_deposit_script,
    deposit_address = :client2hub_deposit_address,
    expire_time = :expire_time
WHERE
    id = :client2hub_channel_id;


-- update hub connection
UPDATE HubConnection SET complete = 1 WHERE handle = :handle;
