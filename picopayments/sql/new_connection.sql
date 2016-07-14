BEGIN TRANSACTION;

-- insert current terms if they do not already exist
INSERT INTO Terms (
    asset, setup_ttl, deposit_limit, deposit_ratio,
    timeout_limit, fee_setup, fee_sync
)
SELECT
    :asset, :setup_ttl, :deposit_limit, :deposit_ratio,
    :timeout_limit, :fee_setup, :fee_sync
WHERE NOT EXISTS(
    SELECT id FROM Terms WHERE
        asset = :asset and 
        setup_ttl = :setup_ttl and
        deposit_limit = :deposit_limit and 
        deposit_ratio = :deposit_ratio and
        timeout_limit = :timeout_limit and 
        fee_setup = :fee_setup and
        fee_sync = :fee_sync -- FIXME just check if newest matches
);

-- insert new key for every connection (avoid reusing keys)
INSERT INTO Keys (asset, pubkey, wif, address)
VALUES (:asset, :hub_pubkey, :hub_wif, :hub_address);

-- insert spend secret for receive channel
INSERT INTO Secrets (hash, value) VALUES (:secret_hash, :secret_value);

-- insert send micropayment channel
INSERT INTO MicropaymentChannel (
    deposit_script, cached_deposit_address, cached_payee_pubkey,
    cached_payer_pubkey, cached_payee_address, cached_payer_address,
    cached_expire_time, cached_spend_secret_hash
) VALUES (
    :send_deposit_script, :send_cached_deposit_address,
    :client_pubkey, :hub_pubkey, :client_address, :hub_address,
    :send_cached_expire_time, :send_cached_spend_secret_hash
);

-- insert receive micropayment channel
INSERT INTO MicropaymentChannel (
    deposit_script, cached_deposit_address, cached_payee_pubkey,
    cached_payer_pubkey, cached_payee_address, cached_payer_address,
    cached_expire_time, cached_spend_secret_hash
) VALUES (
    :recv_deposit_script, :recv_cached_deposit_address,
    :hub_pubkey, :client_pubkey, :hub_address, :client_address,
    :recv_cached_expire_time, :secret_hash
);

-- insert hub connection
INSERT INTO HubConnection(
    handle, asset, send_channel_id, recv_channel_id, terms_id, hub_rpc_url
) VALUES (
    :handle, :asset,
    (
        -- created send micropayment channel
        SELECT id FROM MicropaymentChannel WHERE 
            deposit_script = :recv_deposit_script -- unique
    ), 
    (
        -- created receive micropayment channel
        SELECT id FROM MicropaymentChannel WHERE 
            deposit_script = :send_deposit_script -- unique
    ), 
    (
        -- terms at the time of the request
        SELECT id FROM Terms WHERE
            asset = :asset and
            setup_ttl = :setup_ttl and
            deposit_limit = :deposit_limit and
            deposit_ratio = :deposit_ratio and
            timeout_limit = :timeout_limit and
            fee_setup = :fee_setup and
            fee_sync = :fee_sync
    ),
    :hub_rpc_url
);

COMMIT;
