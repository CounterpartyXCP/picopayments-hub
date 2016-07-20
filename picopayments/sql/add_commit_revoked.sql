INSERT INTO CommitRevoked (
    channel_id, script, revoke_secret, commit_address, delay_time
) VALUES (
    :channel_id, :script, :revoke_secret, :commit_address, :delay_time
);
