BEGIN TRANSACTION;

CREATE TABLE Terms(
    id                          INTEGER NOT NULL PRIMARY KEY,
    asset                       TEXT NOT NULL,
    setup_ttl                   INTEGER NOT NULL,       -- blocks
    deposit_limit               INTEGER NOT NULL,       -- satoshis
    deposit_ratio               REAL NOT NULL,
    timeout_limit               INTEGER NOT NULL,       -- blocks
    fee_setup                   INTEGER NOT NULL,       -- satoshis
    fee_sync                    INTEGER NOT NULL,       -- satoshis
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

CREATE TABLE Keys(
    asset                       TEXT NOT NULL,
    pubkey                      TEXT NOT NULL UNIQUE,   -- hex public key
    wif                         TEXT NOT NULL UNIQUE,   -- bitcoin wif
    address                     TEXT NOT NULL UNIQUE,   -- bitcoin address
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

CREATE TABLE Secrets(
    hash                        TEXT NOT NULL UNIQUE,   -- hex
    value                       TEXT NOT NULL UNIQUE    -- hex
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
    unused_revoke_secret_hash   TEXT DEFAULT NULL,      -- hex (send only)
    meta_complete               BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE HubConnection(
    handle                      TEXT NOT NULL UNIQUE,   -- hex
    asset                       TEXT NOT NULL,
    send_channel_id             INTEGER NOT NULL,
    recv_channel_id             INTEGER NOT NULL,
    terms_id                    INTEGER NOT NULL,
    hub_rpc_url                 TEXT,                   -- client is a hub

    FOREIGN KEY(send_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(recv_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

CREATE TABLE CommitRequested(
    channel_id                  INTEGER NOT NULL,
    revoke_secret_hash          TEXT NOT NULL,          -- hex

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE CommitActive(
    channel_id                  INTEGER NOT NULL,
    rawtx                       TEXT NOT NULL UNIQUE,   -- hex
    script                      TEXT NOT NULL UNIQUE,   -- hex
    commit_address              TEXT NOT NULL UNIQUE,   -- bitcoin address
    delay_time                  INTEGER NOT NULL,       -- blocks
    revoke_secret_hash          TEXT NOT NULL,          -- hex

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE CommitRevoked(
    channel_id                  INTEGER NOT NULL,
    script                      TEXT NOT NULL UNIQUE,   -- hex
    revoke_secret               TEXT NOT NULL,          -- hex
    commit_address              TEXT NOT NULL UNIQUE,   -- bitcoin address
    delay_time                  INTEGER NOT NULL,       -- blocks

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

COMMIT;
