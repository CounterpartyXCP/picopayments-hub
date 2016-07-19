BEGIN TRANSACTION;

-- update hub connection
UPDATE HubConnection SET
    next_revoke_secret_hash = :next_revoke_secret_hash
WHERE
    handle = :handle;

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

-- add revoke secret hash to commits requested (emulate mpc_request_commit)
INSERT INTO CommitRequested (channel_id, revoke_secret_hash)
VALUES (:recv_channel_id, :secret_hash);

-- save revoke secret
INSERT INTO Secrets (hash, value) VALUES (:secret_hash, :secret_value);

COMMIT;
