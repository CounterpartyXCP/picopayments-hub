SELECT 
    HubConnection.asset as 'asset',
    HubConnection.handle as 'handle', 
    HubConnection.hub_rpc_url as 'client_url',
    MPC_C2H.deposit_script as 'client2hub_deposit_script',
    MPC_H2C.deposit_script as 'hub2client_deposit_script',
    Keys.wif as 'wif'
FROM HubConnection 
    INNER JOIN MicropaymentChannel AS MPC_H2C
        ON MPC_H2C.id = HubConnection.hub2client_channel_id
    INNER JOIN MicropaymentChannel AS MPC_C2H
        ON MPC_C2H.id = HubConnection.client2hub_channel_id
    INNER JOIN Keys ON MPC_H2C.payer_pubkey = Keys.pubkey;
