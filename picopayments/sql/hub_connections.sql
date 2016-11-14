SELECT 
    HubConnection.asset as 'asset',
    HubConnection.handle as 'handle', 
    HubConnection.hub_rpc_url as 'client_url',
    MPC_C2H.deposit_script as 'c2h_deposit_script',
    MPC_H2C.deposit_script as 'h2c_deposit_script',
    Keys.wif as 'wif'
FROM HubConnection 
    INNER JOIN MicropaymentChannel AS MPC_H2C
        ON MPC_H2C.id = HubConnection.h2c_channel_id
    INNER JOIN MicropaymentChannel AS MPC_C2H
        ON MPC_C2H.id = HubConnection.c2h_channel_id
    INNER JOIN Keys ON MPC_H2C.payer_pubkey = Keys.pubkey
WHERE
    HubConnection.complete != 0 and HubConnection.closed == 0;
