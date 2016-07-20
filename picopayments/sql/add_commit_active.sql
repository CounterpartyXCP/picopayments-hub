INSERT INTO CommitActive (
    channel_id, rawtx, script, commit_address,
    delay_time, revoke_secret_hash
) VALUES (
    :channel_id, :rawtx, :script, :commit_address,
    :delay_time, :revoke_secret_hash
);
