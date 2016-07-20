-- update send channel
UPDATE MicropaymentChannel SET
    deposit_script = :send_deposit_script,
    deposit_address = :send_deposit_address,
    expire_time = :expire_time,
    meta_complete = 1
WHERE
    id = :send_channel_id;

-- update receive channel
UPDATE MicropaymentChannel SET
    deposit_script = :recv_deposit_script,
    deposit_address = :recv_deposit_address,
    expire_time = :expire_time,
    meta_complete = 1
WHERE
    id = :recv_channel_id;
