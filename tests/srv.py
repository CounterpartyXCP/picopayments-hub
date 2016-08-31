import os
import shutil
import unittest
import tempfile
from pycoin.key import validate
from picopayments import srv
from picopayments import etc
from picopayments import lib
from picopayments import __version__


CP_URL = "http://139.59.214.74:14000/api/"


class TestSRV(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_terms_testnet(self):
        terms = srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL),
            "--terms"
        ], serve=False)
        self.assertIsNotNone(terms)
        self.assertEqual(terms, lib.TERMS["TESTNET"])

    def test_terms_mainnet(self):
        terms = srv.main([
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL),
            "--terms"
        ], serve=False)
        self.assertIsNotNone(terms)
        self.assertEqual(terms, lib.TERMS["MAINNET"])

    def test_funding_testnet(self):
        addresses = srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL),
            "--funding"
        ], serve=False)
        self.assertIsNotNone(addresses)
        self.assertTrue(len(addresses) == 3)
        for address in addresses:
            validate.is_address_valid(
                address, allowable_netcodes=[etc.netcode]
            )

    def test_funding_mainnet(self):
        addresses = srv.main([
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL),
            "--funding"
        ], serve=False)
        self.assertIsNotNone(addresses)
        self.assertTrue(len(addresses) == 3)
        for address in addresses:
            validate.is_address_valid(
                address, allowable_netcodes=[etc.netcode]
            )

    def test_version(self):
        version = srv.main([
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL),
            "--version"
        ], serve=False)
        self.assertEqual(version, __version__)


if __name__ == "__main__":
    unittest.main()
