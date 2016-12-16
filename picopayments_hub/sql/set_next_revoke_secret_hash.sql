UPDATE HubConnection SET
    next_revoke_secret_hash = :next_revoke_secret_hash
WHERE
    handle = :handle;
