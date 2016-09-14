BEGIN TRANSACTION;

-- less verbose prefixes
--   client2hub -> c2h
--   hub2client -> h2c


CREATE TABLE _HubConnection(
    id                          INTEGER NOT NULL PRIMARY KEY,
    handle                      TEXT NOT NULL UNIQUE,   -- hex
    asset                       TEXT NOT NULL,
    h2c_channel_id              INTEGER NOT NULL,
    c2h_channel_id              INTEGER NOT NULL,
    terms_id                    INTEGER NOT NULL,
    hub_rpc_url                 TEXT,                   -- client is a hub
    next_revoke_secret_hash     TEXT DEFAULT NULL,      -- hex (for send)
    complete                    BOOLEAN NOT NULL DEFAULT 0,
    closed                      BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(h2c_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(c2h_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

INSERT INTO _HubConnection (
    id, handle, asset, h2c_channel_id, c2h_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash, unixtimestamp, complete, closed
) SELECT 
    id, handle, asset, hub2client_channel_id, client2hub_channel_id,
    terms_id, hub_rpc_url, next_revoke_secret_hash, unixtimestamp,
    complete, closed
FROM HubConnection;

DROP TABLE HubConnection;

CREATE TABLE HubConnection(
    id                          INTEGER NOT NULL PRIMARY KEY,
    handle                      TEXT NOT NULL UNIQUE,   -- hex
    asset                       TEXT NOT NULL,
    h2c_channel_id              INTEGER NOT NULL,
    c2h_channel_id              INTEGER NOT NULL,
    terms_id                    INTEGER NOT NULL,
    hub_rpc_url                 TEXT,                   -- client is a hub
    next_revoke_secret_hash     TEXT DEFAULT NULL,      -- hex (for send)
    complete                    BOOLEAN NOT NULL DEFAULT 0,
    closed                      BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(h2c_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(c2h_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

INSERT INTO HubConnection (
    id, handle, asset, h2c_channel_id, c2h_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash, unixtimestamp, complete, closed
) SELECT 
    id, handle, asset, h2c_channel_id, c2h_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash, unixtimestamp, complete, closed
FROM _HubConnection;

DROP TABLE _HubConnection;
DROP TABLE _TmpTerms;  -- forgot to drop in migration_2.sql

COMMIT;
