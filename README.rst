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


========
Protocol
========

.. image:: channel.png

Deposit Transaction - pay to script:

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


Recover Transaction - script sig:

::
    
    <payer signature> OP_FALSE OP_FALSE

Change Transaction - script sig:

::
    
    <payer signature> <payee secret> OP_TRUE OP_FALSE

Commit Transaction - script sig:

::
    
    <payer signature> <payee signature> OP_TRUE

Commit Transaction - pay to script:

::

    OP_HASH160 <payee secret hash> OP_EQUALVERIFY <payee pubkey> OP_CHECKSIG

Payout Transaction - script sig:

::
    
    <payee signature> <payee secret>

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
