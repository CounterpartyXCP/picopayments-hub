-- update send channel
UPDATE MicropaymentChannel SET
    deposit_script = :h2c_deposit_script,
    deposit_address = :h2c_deposit_address,
    expire_time = :expire_time
WHERE
    id = :h2c_channel_id;

-- update receive channel
UPDATE MicropaymentChannel SET
    deposit_script = :c2h_deposit_script,
    deposit_address = :c2h_deposit_address,
    expire_time = :expire_time
WHERE
    id = :c2h_channel_id;


-- update hub connection
UPDATE HubConnection SET complete = 1 WHERE handle = :handle;
