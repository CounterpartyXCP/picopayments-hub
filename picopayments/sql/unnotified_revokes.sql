SELECT id, revoke_secret FROM CommitRevoked
WHERE NOT(payee_notified) AND channel_id = :channel_id;
