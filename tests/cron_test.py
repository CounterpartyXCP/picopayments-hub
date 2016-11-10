import os
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments import cron


CP_URL = os.environ.get("COUNTERPARTY_URL", "http://127.0.0.1:14000/api/")


class TestCron(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")
        shutil.copytree("tests/fixtures", self.basedir)
        srv.main([
            "--testnet",
            "--basedir={0}".format(self.basedir),
            "--cp_url={0}".format(CP_URL)
        ], serve=False)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @unittest.skip("FIXME")
    def test_close_connections(self):
        closed_connections = cron.close_connections(dryrun=True)
        self.assertEqual(len(closed_connections), 1)
        self.assertTrue(bool(closed_connections))

    @unittest.skip("FIXME")
    def test_fund_deposits(self):
        deposits = cron.fund_deposits(dryrun=True)
        self.assertEqual(len(deposits), 3)
        self.assertTrue(bool(deposits))

    @unittest.skip("FIXME")
    def test_recover_funds(self):
        transactions = cron.recover_funds(dryrun=True)
        self.assertEqual(len(transactions), 0)
        self.assertFalse(bool(transactions))
