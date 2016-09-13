import os
import json
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments import etc
from picopayments import cron


etc.call_local_process = True
CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


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
        with open(os.path.join(self.basedir, "data.json")) as fp:
            self.data = json.load(fp)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_close_connections(self):
        closed_connections = cron.close_connections(publish_tx=False)
        self.assertEqual(len(closed_connections), 1)
        self.assertTrue(bool(closed_connections))

    def test_fund_deposits(self):
        deposits = cron.fund_deposits(publish_tx=False)
        self.assertEqual(len(deposits), 3)
        self.assertTrue(bool(deposits))

    def test_recover_funds(self):
        transactions = cron.recover_funds(publish_tx=False)
        self.assertEqual(len(transactions), 0)
        self.assertFalse(bool(transactions))
