# PicoPayments setup

Tested with Ubuntu 16.04.1 x64. 


## 1. Install dependencies

    sudo apt-get -qq update
    sudo apt-get install -y libxml2-dev
    sudo apt-get install -y gcc
    sudo apt-get install -y python3-dev
    sudo apt-get install -y libffi-dev
    sudo apt-get install -y libssl-dev


## 2. Setup local bitcoin full node

Setup bitcoin full node with addrindex patch

    # Download and extract bitcoin full node
    wget https://github.com/btcdrak/bitcoin/releases/download/v0.12.1-addrindex/bitcoin-0.12.1-addrindex-linux64.tar.gz
    tar -zxvf bitcoin-0.12.1-addrindex-linux64.tar.gz

    # Configure node to keep transaction and address indexes
    cat ~/.bitcoin/bitcoin.conf 
    rpcuser=bitcoinrpcuser
    rpcpassword=bitcoinrpcpass
    daemon=1
    server=1
    txindex=1
    addrindex=1

    # Start bitcoin full node
    bitcoin-0.12.1/bin/bitcoind -testnet -daemon -txindex

    # It will take some time to download the full bitcoin blockchain.
    # Use getinfo api call to check when it has synced.
    bitcoin-0.12.1/bin/bitcoin-cli --rpcuser=bitcoinrpcuser --rpcpassword=bitcoinrpcpass --rpcport=18332 getinfo


## 3. Setup local counterparty node

Setup counterparty node with patched micropayments support.
Best use a screen as the node does not run as a daemon.

    # setup virtualenv
    mkdir counterparty
    cd counterparty
    virtualenv -p /usr/bin/python3 env
    source env/bin/activate

    pip install prettytable==0.7.2
    pip install apsw
    pip install python-dateutil==2.5.3
    pip install Flask-HTTPAuth==3.1.2
    pip install Flask==0.11
    pip install appdirs==1.4.0
    pip install colorlog==2.7.0
    pip install json-rpc==1.10.3
    pip install six>=1.10.0
    pip install pycoin==0.70
    pip install pycrypto==2.6.1
    pip install pysha3==0.3
    pip install pytest==2.9.1
    pip install pytest-cov==2.2.1
    pip install python-bitcoinlib==0.5.1
    pip install requests==2.10.0
    pip install tendo==0.2.8
    pip install xmltodict==0.10.1
    pip install cachetools==1.1.6

    # install counterparty-lib with micropayments patch
    wget https://transfer.sh/V8cQl/counterparty-lib-9.55.0-py3-none-any.whl
    pip install --use-wheel --no-index --find-links=$PWD counterparty-lib
    
    pip install counterparty-cli==1.1.2

    # Start counterparty full node (will take time to process the blockchain)
    counterparty-server --testnet --backend-port=18332 --backend-user=bitcoinrpcuser --backend-password=bitcoinrpcpass start


## 4. Setup picopayments hub

Setup picopayments node with patched micropayments support.
Best use a screen as the node does not run as a daemon.

    # setup virtualenv
    mkdir picopayments
    cd picopayments
    virtualenv -p /usr/bin/python3 env
    source env/bin/activate

    pip install prettytable==0.7.2
    pip install apsw
    pip install python-dateutil==2.5.3
    pip install Flask-HTTPAuth==3.1.2
    pip install Flask==0.11
    pip install appdirs==1.4.0
    pip install colorlog==2.7.0
    pip install json-rpc==1.10.3
    pip install six>=1.10.0
    pip install pycoin==0.70
    pip install pycrypto==2.6.1
    pip install pysha3==0.3
    pip install pytest==2.9.1
    pip install pytest-cov==2.2.1
    pip install python-bitcoinlib==0.5.1
    pip install requests==2.10.0
    pip install tendo==0.2.8
    pip install xmltodict==0.10.1
    pip install cachetools==1.1.6

    # install counterparty-lib with micropayments patch
    wget https://transfer.sh/V8cQl/counterparty-lib-9.55.0-py3-none-any.whl
    pip install --use-wheel --no-index --find-links=$PWD counterparty-lib

    pip install picopayments
    
    # show hub terms (edit terms file as you see fit)
    picopayments --testnet --terms

    # show funding addresses (use to fund the picopayments hub)
    picopayments --testnet --funding

    # Start picopayment node (use generated self signed cert)
    picopayments --testnet --host=0.0.0.0 --cp_url=http://127.0.0.1:14000/api/

    # Start picopayment node (provide existing cert)
    picopayments --testnet --host=0.0.0.0 --cp_url=http://127.0.0.1:14000/api/ --ssl_cert_file=path/to.cert --ssl_pkey_file=path/to.key


## 5. Verify picopayment hub is working.

Run from differnt network to ensure the hub is reachable from the internet.

    curl -X POST https://your.hub.url.or.ip:15000/api/ -H 'Content-Type: application/json; charset=UTF-8' -H 'Accept: application/json, text/javascript' -k --data-binary '{ "jsonrpc": "2.0", "id": 0, "method": "mph_terms" }'
