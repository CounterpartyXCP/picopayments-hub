BEGIN TRANSACTION;

CREATE TABLE Terms(
    id                          INTEGER NOT NULL PRIMARY KEY,
    asset                       TEXT NOT NULL,
    setup_ttl                   INTEGER NOT NULL,                   -- blocks
    deposit_limit               INTEGER NOT NULL,                   -- satoshis
    deposit_ratio               REAL NOT NULL,
    timeout_limit               INTEGER NOT NULL,                   -- blocks
    fee_setup                   INTEGER NOT NULL,                   -- satoshis
    fee_sync                    INTEGER NOT NULL,                   -- satoshis
    timestamp                   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Keys(
    asset                       TEXT NOT NULL,
    pubkey                      TEXT NOT NULL UNIQUE,               -- hex public key
    wif                         TEXT NOT NULL UNIQUE,               -- bitcoin wif
    address                     TEXT NOT NULL UNIQUE                -- bitcoin address
);

CREATE TABLE Secrets(
    hash                        TEXT NOT NULL UNIQUE,               -- hex
    value                       TEXT NOT NULL UNIQUE                -- hex
);

CREATE TABLE MicropaymentChannel(
    id                          INTEGER NOT NULL PRIMARY KEY,
    deposit_script              TEXT NOT NULL UNIQUE,               -- hex
    cached_deposit_address      TEXT NOT NULL UNIQUE,               -- bitcoin address
    cached_payee_pubkey         TEXT NOT NULL,                      -- hex
    cached_payer_pubkey         TEXT NOT NULL,                      -- hex
    cached_payee_address        TEXT NOT NULL,                      -- bitcoin address
    cached_payer_address        TEXT NOT NULL,                      -- bitcoin address
    cached_expire_time          INTEGER NOT NULL,                   -- blocks
    cached_spend_secret_hash    TEXT NOT NULL                       -- hex
);

CREATE TABLE HubConnection(
    handle                      TEXT NOT NULL UNIQUE,               -- hex
    asset                       TEXT NOT NULL,
    send_channel_id             INTEGER,                            -- may be null during setup
    recv_channel_id             INTEGER,                            -- may be null during setup
    terms_id                    INTEGER NOT NULL,

    FOREIGN KEY(send_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(recv_channel_id) REFERENCES MicropaymentChannel(id),
    FOREIGN KEY(terms_id) REFERENCES Terms(id) 
);

CREATE TABLE CommitRequested(
    channel_id                  INTEGER NOT NULL,                   -- may be null during setup
    revoke_secret_hash          TEXT NOT NULL,                      -- hex

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE CommitActive(
    channel_id                  INTEGER NOT NULL,                   -- may be null during setup
    rawtx                       TEXT NOT NULL UNIQUE,               -- hex
    script                      TEXT NOT NULL UNIQUE,               -- hex
    cached_commit_address       TEXT NOT NULL UNIQUE,               -- bitcoin address
    cached_delay_time           INTEGER NOT NULL,                   -- blocks
    cached_revoke_secret_hash   TEXT NOT NULL,                      -- hex

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

CREATE TABLE CommitRevoked(
    channel_id                  INTEGER NOT NULL,                   -- may be null during setup
    script                      TEXT NOT NULL UNIQUE,               -- hex
    revoke_secret               TEXT NOT NULL,                      -- hex
    cached_commit_address       TEXT NOT NULL UNIQUE,               -- bitcoin address
    cached_delay_time           INTEGER NOT NULL,                   -- blocks

    FOREIGN KEY(channel_id) REFERENCES MicropaymentChannel(id) 
);

COMMIT;
