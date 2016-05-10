############
PicoPayments
############

|BuildLink|_ |CoverageLink|_ |LicenseLink|_ |IssuesLink|_


.. |BuildLink| image:: https://travis-ci.org/Storj/picopayments.svg
.. _BuildLink: https://travis-ci.org/Storj/picopayments

.. |CoverageLink| image:: https://coveralls.io/repos/Storj/picopayments/badge.svg
.. _CoverageLink: https://coveralls.io/r/Storj/picopayments

.. |LicenseLink| image:: https://img.shields.io/badge/license-MIT-blue.svg
.. _LicenseLink: https://raw.githubusercontent.com/F483/picopayments/master/LICENSE

.. |IssuesLink| image:: https://img.shields.io/github/issues/F483/picopayments.svg
.. _IssuesLink: https://github.com/F483/picopayments/issues


Trustless micropayment channels for counterparty assets ᕕ( ᐛ )ᕗ


============
Installation
============

::

  pip install picopayments


=====
Usage
=====

---------------------
Fast native functions
---------------------

There is experimental code that will call into OpenSSL for slow functions.
To enable this, set (and export) environment variable PYCOIN_NATIVE=openssl.

::

  $ export PYCOIN_NATIVE=openssl

-------
Example
-------

TODO


========
Protocol
========

.. image:: channel.png


-------------------
Deposit Transaction
-------------------

The deposit transaction ensures the payee cannot spend the funds while
the channel is open.

The pay to script allows for three possible outcoms:

 - The payer can recover the deposit after a timeout if no commit was made.
 - Both parties commit and close the channel.
 - The payer collects the change after the payee publishes the spend secret.

**The commit transaction spend secret must be the same as the deposit
transaction spend secret!**

pay to script:

::

    OP_IF
        2 <payer pubkey> <payee pubkey> 2 OP_CHECKMULTISIG
    OP_ELSE
        OP_IF
            OP_HASH160 <spend secret hash> OP_EQUALVERIFY
            <payer pubkey> OP_CHECKSIG
        OP_ELSE
            <expire time> OP_CHECKSEQUENCEVERIFY OP_DROP
            <payer pubkey> OP_CHECKSIG
        OP_ENDIF
    OP_ENDIF


-------------------
Timeout Transaction 
-------------------

The timeout transaction is used by the payee to recover the and funds after
the channel reaches a timeout. This is to prevent funds being lost should
the payee be hit by a bus.

script sig:

::
    
    <payer signature> OP_FALSE OP_FALSE


------------------
Change Transaction 
------------------

After the commit transaction has been published on the blockchain, the
payee must reveal the spend secret to spend the committed funds. The payer
can then recover the change from the channel before it times out by using the
revealed spend secret.

script sig:

::
    
    <payer signature> <spend secret> OP_TRUE OP_FALSE

------------------
Commit Transaction 
------------------

The commit transaction is used to transfer funds and prevent a race condition
between the payee recovering the payout and the payer recovering the change.

Every time the payer wishes to transfer funds to the payee, the output amount
of the transaction is increased. The payee then signs and shares it.

To ensure the payer can recover the change without having to wait for the
channel to timeout, the payee must reveal the spend secret when spending the
payout. **The commit transaction spend secret must be the same as the deposit
transaction spend secret!**

The transaction also enables spending by the payer if the transaction was
revoked by the payee (revealed the revolk signature). This prevents the payee
from publishing a revoked transaction.


script sig:

::
    
    <payer signature> <payee signature> OP_TRUE

pay to script:

::

    OP_IF
        OP_HASH160 <spend secret hash> OP_EQUALVERIFY
        <payee pubkey> OP_CHECKSIG
    OP_ELSE
        OP_HASH160 <revoke secret hash> OP_EQUALVERIFY
        <payer pubkey> OP_CHECKSIG
    OP_ENDIF


------------------
Payout Transaction 
------------------

The payout transaction is used by the payee to spend the commited funds. In
order to spend the funds the payee must reveal the spend secret, this ensures
the payer can recover the change.

The payout can only be done after a delay to ensure the payer has time to
react if the payee tries to publish a revoked commit transaction.

script sig:

::
    
    <payee signature> <spend secret> OP_TRUE

    
------------------
Revoke Transaction 
------------------

If the payee tries to publish a revoked commit transaction, the payer can
recover the funds during the payout delay using the revolk secret.

script sig:

::
    
    <payer signature> <revoke secret> OP_FALSE
