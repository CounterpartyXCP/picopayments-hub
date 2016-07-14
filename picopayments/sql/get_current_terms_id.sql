BEGIN TRANSACTION;

-- Insert current terms if they do not already exist.
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
        fee_sync = :fee_sync
);

-- Get terms id for cursor output.
SELECT id FROM Terms WHERE
    asset = :asset and 
    setup_ttl = :setup_ttl and
    deposit_limit = :deposit_limit and 
    deposit_ratio = :deposit_ratio and
    timeout_limit = :timeout_limit and 
    fee_setup = :fee_setup and
    fee_sync = :fee_sync;

COMMIT;
