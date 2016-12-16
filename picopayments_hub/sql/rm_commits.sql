DELETE FROM CommitRequested WHERE channel_id = :channel_id;
DELETE FROM CommitActive WHERE channel_id = :channel_id;
DELETE FROM CommitRevoked WHERE channel_id = :channel_id;
