BEGIN TRANSACTION;

PRAGMA defer_foreign_keys = ON;

-- move meta_closed and meta_complete from channel to connection

CREATE TABLE _TmpHubConnection(
    id                          INTEGER NOT NULL PRIMARY KEY,
    handle                      TEXT NOT NULL UNIQUE,   -- hex
    asset                       TEXT NOT NULL,
    hub2client_channel_id       INTEGER NOT NULL,
    client2hub_channel_id       INTEGER NOT NULL,
    terms_id                    INTEGER NOT NULL,
    hub_rpc_url                 TEXT,                   -- client is a hub
    next_revoke_secret_hash     TEXT DEFAULT NULL,      -- hex (for send)
    complete                    BOOLEAN NOT NULL DEFAULT 0,
    closed                      BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(hub2client_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(client2hub_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

INSERT INTO _TmpHubConnection (
    id, handle, asset, hub2client_channel_id, client2hub_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash, complete, closed, unixtimestamp
) SELECT 
    id, handle, asset, hub2client_channel_id, client2hub_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash,
    (
        SELECT meta_complete FROM MicropaymentChannel 
        WHERE MicropaymentChannel.id = HubConnection.hub2client_channel_id
    ),
    0,
    unixtimestamp
FROM HubConnection;

DROP TABLE HubConnection;

CREATE TABLE HubConnection(
    id                          INTEGER NOT NULL PRIMARY KEY,
    handle                      TEXT NOT NULL UNIQUE,   -- hex
    asset                       TEXT NOT NULL,
    hub2client_channel_id       INTEGER NOT NULL,
    client2hub_channel_id       INTEGER NOT NULL,
    terms_id                    INTEGER NOT NULL,
    hub_rpc_url                 TEXT,                   -- client is a hub
    next_revoke_secret_hash     TEXT DEFAULT NULL,      -- hex (for send)
    complete                    BOOLEAN NOT NULL DEFAULT 0,
    closed                      BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(hub2client_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(client2hub_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

INSERT INTO HubConnection (
    id, handle, asset, hub2client_channel_id, client2hub_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash, complete, closed, unixtimestamp
) SELECT 
    id, handle, asset, hub2client_channel_id, client2hub_channel_id, terms_id,
    hub_rpc_url, next_revoke_secret_hash, complete, closed, unixtimestamp
FROM _TmpHubConnection;

DROP TABLE _TmpHubConnection;


CREATE TABLE _TmpMicropaymentChannel(
    id                          INTEGER NOT NULL PRIMARY KEY,
    deposit_script              TEXT,                   -- hex
    deposit_address             TEXT,                   -- bitcoin address
    payee_pubkey                TEXT NOT NULL,          -- hex
    payer_pubkey                TEXT NOT NULL,          -- hex
    payee_address               TEXT NOT NULL,          -- bitcoin address
    payer_address               TEXT NOT NULL,          -- bitcoin address
    expire_time                 INTEGER,                -- blocks
    spend_secret_hash           TEXT NOT NULL,          -- hex
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

INSERT INTO _TmpMicropaymentChannel (
    id, deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash,
    unixtimestamp
) SELECT 
    id, deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash,
    unixtimestamp
FROM MicropaymentChannel;

DROP TABLE MicropaymentChannel;

CREATE TABLE MicropaymentChannel(
    id                          INTEGER NOT NULL PRIMARY KEY,
    deposit_script              TEXT,                   -- hex
    deposit_address             TEXT,                   -- bitcoin address
    payee_pubkey                TEXT NOT NULL,          -- hex
    payer_pubkey                TEXT NOT NULL,          -- hex
    payee_address               TEXT NOT NULL,          -- bitcoin address
    payer_address               TEXT NOT NULL,          -- bitcoin address
    expire_time                 INTEGER,                -- blocks
    spend_secret_hash           TEXT NOT NULL,          -- hex
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

INSERT INTO MicropaymentChannel (
    id, deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash,
    unixtimestamp
) SELECT 
    id, deposit_script, deposit_address, payee_pubkey, payer_pubkey,
    payee_address, payer_address, expire_time, spend_secret_hash,
    unixtimestamp
FROM _TmpMicropaymentChannel;

DROP TABLE _TmpMicropaymentChannel;

COMMIT;
