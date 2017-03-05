-- insert current terms if they do not the latest saved
INSERT INTO Terms (
    asset, 
    deposit_max,
    deposit_min,
    deposit_ratio,
    expire_max,
    expire_min,
    sync_fee
)
SELECT
    :asset, 
    :deposit_max,
    :deposit_min,
    :deposit_ratio,
    :expire_max,
    :expire_min,
    :sync_fee

WHERE NOT EXISTS(
    SELECT id FROM Terms WHERE
        asset = :asset and
        deposit_max = :deposit_max and
        deposit_min = :deposit_min and
        deposit_ratio = :deposit_ratio and
        expire_max = :expire_max and
        expire_min = :expire_min and
        sync_fee = :sync_fee
);

-- insert spend secret for receive channel
INSERT INTO Secrets (hash, value) VALUES (:secret_hash, :secret_value);

-- insert h2c micropayment channel
INSERT INTO MicropaymentChannel (
    deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash, handle
) VALUES (
    NULL, NULL, :client_pubkey, :hub_pubkey, :client_address,
    :hub_address, NULL, :h2c_spend_secret_hash, :handle
);

-- insert c2h micropayment channel
INSERT INTO MicropaymentChannel (
    deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash, handle
) VALUES (
    NULL, NULL, :hub_pubkey, :client_pubkey, :hub_address,
    :client_address, :c2h_expire_time, :secret_hash, :handle
);

-- insert hub connection
INSERT INTO HubConnection(
    handle, asset, h2c_channel_id, c2h_channel_id, terms_id, hub_rpc_url
) VALUES (
    :handle, :asset,
    (
        -- created send micropayment channel (relies on unique hub_pubkey)
        SELECT id FROM MicropaymentChannel 
        WHERE payee_pubkey = :client_pubkey and handle = :handle
    ),
    (
        -- created receive micropayment channel (relies on unique hub_pubkey)
        SELECT id FROM MicropaymentChannel 
        WHERE payer_pubkey = :client_pubkey and handle = :handle
    ),
    (
        -- terms at the time of the request
        SELECT id FROM Terms WHERE
            asset = :asset and
            deposit_max = :deposit_max and
            deposit_min = :deposit_min and
            deposit_ratio = :deposit_ratio and
            expire_max = :expire_max and
            expire_min = :expire_min and
            sync_fee = :sync_fee
    ),
    :hub_rpc_url
);
