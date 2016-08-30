SELECT id, rawtx, script FROM CommitActive WHERE NOT(payee_notified) AND channel_id = :channel_id;
