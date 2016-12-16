BEGIN TRANSACTION;

-- setup initial db schema

CREATE TABLE Terms(
    id                          INTEGER NOT NULL PRIMARY KEY,
    asset                       TEXT NOT NULL,
    setup_ttl                   INTEGER NOT NULL,       -- blocks
    deposit_limit               INTEGER NOT NULL,       -- satoshis
    deposit_ratio               REAL NOT NULL,
    timeout_limit               INTEGER NOT NULL,       -- blocks
    sync_fee                    INTEGER NOT NULL,       -- satoshis
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

CREATE TABLE Keys(
    id                          INTEGER NOT NULL PRIMARY KEY,
    asset                       TEXT NOT NULL,
    pubkey                      TEXT NOT NULL UNIQUE,   -- hex public key
    wif                         TEXT NOT NULL UNIQUE,   -- bitcoin wif
    address                     TEXT NOT NULL UNIQUE,   -- bitcoin address
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

CREATE TABLE Secrets(
    id                          INTEGER NOT NULL PRIMARY KEY,
    hash                        TEXT NOT NULL UNIQUE,   -- hex
    value                       TEXT NOT NULL UNIQUE,   -- hex
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

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
    meta_complete               BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

CREATE TABLE HubConnection(
    id                          INTEGER NOT NULL PRIMARY KEY,
    handle                      TEXT NOT NULL UNIQUE,   -- hex
    asset                       TEXT NOT NULL,
    hub2client_channel_id       INTEGER NOT NULL,
    client2hub_channel_id       INTEGER NOT NULL,
    terms_id                    INTEGER NOT NULL,
    hub_rpc_url                 TEXT,                   -- client is a hub
    next_revoke_secret_hash     TEXT DEFAULT NULL,      -- hex (for send)
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(hub2client_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(client2hub_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

CREATE TABLE CommitRequested(
    id                          INTEGER NOT NULL PRIMARY KEY,
    channel_id                  INTEGER NOT NULL,
    revoke_secret_hash          TEXT NOT NULL,          -- hex
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE CommitActive(
    id                          INTEGER NOT NULL PRIMARY KEY,
    channel_id                  INTEGER NOT NULL,
    rawtx                       TEXT NOT NULL UNIQUE,   -- hex
    script                      TEXT NOT NULL UNIQUE,   -- hex
    commit_address              TEXT NOT NULL UNIQUE,   -- bitcoin address
    delay_time                  INTEGER NOT NULL,       -- blocks
    revoke_secret_hash          TEXT NOT NULL,          -- hex
    payee_notified              BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE CommitRevoked(
    id                          INTEGER NOT NULL PRIMARY KEY,
    channel_id                  INTEGER NOT NULL,
    script                      TEXT NOT NULL UNIQUE,   -- hex
    revoke_secret               TEXT NOT NULL,          -- hex
    commit_address              TEXT NOT NULL UNIQUE,   -- bitcoin address
    delay_time                  INTEGER NOT NULL,       -- blocks
    payee_notified              BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')),

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE Payment(
    id                          INTEGER NOT NULL PRIMARY KEY,
    amount                      INTEGER NOT NULL,       -- satoshis
    payer_handle                TEXT,                   -- hex (NULL -> hub)
    payee_handle                TEXT,                   -- hex (NULL -> hub)
    token                       TEXT NOT NULL,          -- hex
    payee_notified              BOOLEAN NOT NULL DEFAULT 0,
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

COMMIT;
