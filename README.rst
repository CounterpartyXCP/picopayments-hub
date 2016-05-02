#################################################
PicoPayments - Counterparty Micropayment Channels
#################################################


|BuildLink|_ |CoverageLink|_ |LicenseLink|_ |IssuesLink|_


.. |BuildLink| image:: https://travis-ci.org/Storj/picopayments.svg
.. _BuildLink: https://travis-ci.org/Storj/picopayments

.. |CoverageLink| image:: https://coveralls.io/repos/Storj/picopayments/badge.svg
.. _CoverageLink: https://coveralls.io/r/Storj/picopayments

.. |LicenseLink| image:: https://img.shields.io/badge/license-MIT-blue.svg
.. _LicenseLink: https://raw.githubusercontent.com/F483/picopayments/master/LICENSE

.. |IssuesLink| image:: https://img.shields.io/github/issues/F483/picopayments.svg
.. _IssuesLink: https://github.com/F483/picopayments/issues


============
Installation
============

::

  pip install picopayments


=========================
Use fast native functions
=========================

There is experimental code that will call into OpenSSL for slow functions.
To enable this, set (and export) environment variable PYCOIN_NATIVE=openssl.

::

  $ export PYCOIN_NATIVE=openssl

=====
Usage
=====

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
 - The payer collects the change after the payee publishes the secret.

**The commit transaction secret must be the same as the deposit
transaction secret!**

pay to script:

::

    OP_IF
        2 <payer pubkey> <payee pubkey> 2 OP_CHECKMULTISIG
    OP_ELSE
        OP_IF
            OP_HASH160 <payee secret hash> OP_EQUALVERIFY
            <payer pubkey> OP_CHECKSIG
        OP_ELSE
            <expire time> OP_CHECKSEQUENCEVERIFY OP_DROP
            <payer pubkey> OP_CHECKSIG
        OP_ENDIF
    OP_ENDIF


-------------------
Recover Transaction 
-------------------

The recover transaction is used by the payee to recover the and funds after
the channel reaches a timeout. This is to prevent funds being lost should
the payee be hit by a bus.

script sig:

::
    
    <payer signature> OP_FALSE OP_FALSE


------------------
Change Transaction 
------------------

After the commit transaction has been published on the blockchain, the
payee must reveal the secret to spend the committed funds. The payer can
then recover the change from the channel before it times out by using the
revealed secret.

script sig:

::
    
    <payer signature> <payee secret> OP_TRUE OP_FALSE

------------------
Commit Transaction 
------------------

The commit transaction is used to transfer funds and prevent a race condition
between the payee recovering the payout and the payer recovering the change.

Every time the payer wishes to transfer funds to the payee, the output amount
of the transaction is increased. The payee then signs and shares it.

To ensure the payer can recover the change without having to wait for the
channel to timeout, the payee must reveal the secret when spending the
payout. **The commit transaction secret must be the same as the deposit
transaction secret!**

script sig:

::
    
    <payer signature> <payee signature> OP_TRUE

pay to script:

::

    OP_HASH160 <payee secret hash> OP_EQUALVERIFY <payee pubkey> OP_CHECKSIG


------------------
Payout Transaction 
------------------

The payout transaction is used by the payee to spend the commited funds. In
order to spend the funds the payee must reveal the secret, this ensures
the payer can ecover the change.

script sig:

::
    
    <payee signature> <payee secret>


