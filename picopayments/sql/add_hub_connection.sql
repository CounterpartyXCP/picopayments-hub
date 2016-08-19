-- insert current terms if they do not the latest saved
INSERT INTO Terms (
    asset, setup_ttl, deposit_limit, deposit_ratio,
    timeout_limit, sync_fee
)
SELECT
    :asset, :setup_ttl, :deposit_limit, :deposit_ratio,
    :timeout_limit, :sync_fee
WHERE NOT EXISTS(
    SELECT id FROM Terms WHERE
        asset = :asset and
        setup_ttl = :setup_ttl and
        deposit_limit = :deposit_limit and
        deposit_ratio = :deposit_ratio and
        timeout_limit = :timeout_limit and
        sync_fee = :sync_fee -- FIXME just check if newest matches
);

-- insert new key for every connection (avoid reusing keys)
INSERT INTO Keys (asset, pubkey, wif, address)
VALUES (:asset, :hub_pubkey, :hub_wif, :hub_address);

-- insert spend secret for receive channel
INSERT INTO Secrets (hash, value) VALUES (:secret_hash, :secret_value);

-- insert send micropayment channel
INSERT INTO MicropaymentChannel (
    deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash
) VALUES (
    NULL, NULL, :client_pubkey, :hub_pubkey, :client_address,
    :hub_address, NULL, :hub2client_spend_secret_hash
);

-- insert receive micropayment channel
INSERT INTO MicropaymentChannel (
    deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash
) VALUES (
    NULL, NULL, :hub_pubkey, :client_pubkey, :hub_address,
    :client_address, :client2hub_expire_time, :secret_hash
);

-- insert hub connection
INSERT INTO HubConnection(
    handle, asset, hub2client_channel_id,
    client2hub_channel_id, terms_id, hub_rpc_url
) VALUES (
    :handle, :asset,
    (
        -- created send micropayment channel (relies on unique hub_pubkey)
        SELECT id FROM MicropaymentChannel WHERE payer_pubkey = :hub_pubkey
    ),
    (
        -- created receive micropayment channel (relies on unique hub_pubkey)
        SELECT id FROM MicropaymentChannel WHERE payee_pubkey = :hub_pubkey
    ),
    (
        -- terms at the time of the request
        SELECT id FROM Terms WHERE
            asset = :asset and
            setup_ttl = :setup_ttl and
            deposit_limit = :deposit_limit and
            deposit_ratio = :deposit_ratio and
            timeout_limit = :timeout_limit and
            sync_fee = :sync_fee  -- FIXME select newest
    ),
    :hub_rpc_url
);
