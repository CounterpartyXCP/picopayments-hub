INSERT INTO CommitRevoked (
    channel_id, script, revoke_secret, commit_address,
    delay_time, payee_notified
) VALUES (
    :channel_id, :script, :revoke_secret, :commit_address,
    :delay_time, :payee_notified
);
