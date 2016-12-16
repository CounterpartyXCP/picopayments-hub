BEGIN TRANSACTION;

PRAGMA defer_foreign_keys = ON;

CREATE TABLE _TmpTerms(
    id                          INTEGER NOT NULL PRIMARY KEY,
    asset                       TEXT NOT NULL,
    deposit_max                 INTEGER NOT NULL,       -- satoshis
    deposit_min                 INTEGER NOT NULL,       -- satoshis
    deposit_ratio               REAL NOT NULL,
    expire_max                  INTEGER NOT NULL,       -- satoshis
    expire_min                  INTEGER NOT NULL,       -- satoshis
    sync_fee                    INTEGER NOT NULL,       -- satoshis
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

INSERT INTO _TmpTerms (
    id, asset, deposit_max, deposit_min, deposit_ratio,
    expire_max, expire_min, sync_fee, unixtimestamp
) SELECT 
    id, asset, deposit_limit, 0, deposit_ratio,
    timeout_limit, 0, sync_fee, unixtimestamp
FROM Terms;

DROP TABLE Terms;

CREATE TABLE Terms(
    id                          INTEGER NOT NULL PRIMARY KEY,
    asset                       TEXT NOT NULL,
    deposit_max                 INTEGER NOT NULL,       -- satoshis
    deposit_min                 INTEGER NOT NULL,       -- satoshis
    deposit_ratio               REAL NOT NULL,
    expire_max                  INTEGER NOT NULL,       -- satoshis
    expire_min                  INTEGER NOT NULL,       -- satoshis
    sync_fee                    INTEGER NOT NULL,       -- satoshis
    unixtimestamp               timestamp default (strftime('%s', 'now')) 
);

INSERT INTO Terms (
    id, asset, deposit_max, deposit_min, deposit_ratio,
    expire_max, expire_min, sync_fee, unixtimestamp
) SELECT 
    id, asset, deposit_max, deposit_min, deposit_ratio,
    expire_max, expire_min, sync_fee, unixtimestamp
FROM _TmpTerms;

COMMIT;
