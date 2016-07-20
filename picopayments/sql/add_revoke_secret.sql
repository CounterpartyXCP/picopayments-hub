
-- emulate mpc_request_commit
INSERT INTO CommitRequested (
    channel_id, revoke_secret_hash
) VALUES (
    :channel_id, :secret_hash
);

-- save secret value and hash
INSERT INTO Secrets (hash, value) VALUES (:secret_hash, :secret_value);
