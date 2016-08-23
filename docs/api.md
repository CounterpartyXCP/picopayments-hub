# mpc_hub_connections

Audit hubs liquidity to determan if a transfer is likely to succeed.

Each entry is signed by the hub to prove it controls the keypair.

Optionally the entries can be limited to a set of provided clients and assets.

    Arguments: {
        "handles": ["handle"],
        "assets": ["asset"]
    }

    Response: [{
        "asset": "asset",
        "handle": "handle",
        "client_url": "url" or null,
        "client2hub_deposit_script": "hex",
        "hub2client_deposit_script": "hex",
        "pubkey": "hub pubkey hex",
        "signature": "hub signature hex"
    }]


# mpc_hub_terms

Get current terms of the hub.

    Arguments: {
        "assets": [asset]
    }

    Response: {
        "asset": {
            "setup_ttl": blocks,  # client deposit must be confirmed within
            "deposit_limit": satoshis,  # max server will invest in channel
            "deposit_ratio": float,  # deposit ratio compared to client
            "timeout_limit": blocks,  # max timeout server will set
            "sync_fee": satoshisa  # fee per sync
        }
    }


# mpc_hub_request

Exchange spend secrets and pubkeys for channel.

Channel culled if deposit not made fast enough.

    Arguments: {
        "asset": asset,
        "pubkey": "hex",
        "signature": "hex",
        "spend_secret_hash": "hex"  # hub to client channel
        "url": "url" or None  # client is itself a payment hub
    }

    Response: {
        "handle": "hex",
        "spend_secret_hash": "hex",  # client to hub channel
        "pubkey": "hex",
        "signature": "hex",
        "channel_terms": {
            "setup_ttl": blocks,  # client deposit must be confirmed within
            "deposit_limit": satoshis,  # max server will invest in channel
            "deposit_ratio": float,  # deposit ratio compared to client
            "timeout_limit": blocks,  # max timeout server will set
            "sync_fee": satoshisa  # fee per sync
        }
    }


# mpc_hub_deposit

Exchange depsoit scripts. Hub waits with funding deposit until client deposit is confirmed.

Hub will fund deposit according to the deposit ratio given in the terms.

Channel culled if client deposit not made fast enough.

    Arguments: {
        "handle": "hex",
        "pubkey": "hex",
        "signature": "hex",
        "deposit_script": "hex",  # client to hub
        "next_revoke_secret_hash": "hex"  # hub to client channel
    }

    Response: {
        "pubkey": "hex",
        "signature": "hex",
        "deposit_script": "hex",  # hub to client
        "next_revoke_secret_hash": "hex"  # client to hub channel
    }


# mpc_hub_sync

    Arguments: {
        "handle": "hex",
        "pubkey": "hex",
        "signature": "hex",
        "sends": [{
            "payee_handle": "hex", 
            "amount": satoshis, 
            "token": "hex"
        }],
        "commit": {"rawtx": "hex", "script": "hex"},
        "revokes": ["secrets"],
        "next_revoke_secret_hash": "hex"  # hub to client channel
    }

    Response: {
        "pubkey": "hex",
        "signature": "hex",
        "receive": [{
            "payer_handle": "hex", 
            "amount": satoshis, 
            "token": "hex"
        }],
        "commit": {"rawtx": "hex", "script": "hex"},
        "revokes": ["hex"],
        "next_revoke_secret_hash": "hex"  # client to hub channel
    }
