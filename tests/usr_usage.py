import os
import json
import shutil
import unittest
import tempfile
from picopayments import etc
from picopayments import srv
from picopayments import HubClient


etc.call_local_process = True
CP_URL = os.environ.get("COUNTERPARTY_URL", "http://139.59.214.74:14000/api/")


class TestUsr(unittest.TestCase):

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

    def test_standard_usage(self):

        # setup
        alpha = HubClient.deserialize(self.data["connections"]["alpha"])
        beta = HubClient.deserialize(self.data["connections"]["beta"])
        gamma = HubClient.deserialize(self.data["connections"]["gamma"])
        delta = HubClient.deserialize(self.data["connections"]["delta"])
        epsilon = HubClient.deserialize(self.data["connections"]["epsilon"])
        zeta = HubClient.deserialize(self.data["connections"]["zeta"])

        # after before status
        alpha_before_status = alpha.get_status()
        beta_before_status = beta.get_status()
        gamma_before_status = gamma.get_status()
        delta_before_status = delta.get_status()
        epsilon_before_status = epsilon.get_status()
        zeta_before_status = zeta.get_status()

        # can send multiple payments
        alpha.micro_send(beta.handle, 5, "0000")
        alpha.micro_send(gamma.handle, 6, "0001")
        self.assertEqual(alpha.sync(), [])
        self.assertEqual(beta.sync(), [{
            "payer_handle": alpha.handle,
            "amount": 5,
            "token": "0000"
        }])
        self.assertEqual(gamma.sync(), [{
            "payer_handle": alpha.handle,
            "amount": 6,
            "token": "0001"
        }])

        # get after status
        alpha_after_status = alpha.get_status()
        beta_after_status = beta.get_status()
        gamma_after_status = gamma.get_status()
        delta_after_status = delta.get_status()
        epsilon_after_status = epsilon.get_status()
        zeta_after_status = zeta.get_status()

        # compare statuses
        alpha_after_status["balance"] == alpha_before_status["balance"] - 12
        beta_after_status["balance"] == beta_before_status["balance"] + 4
        gamma_after_status["balance"] == gamma_before_status["balance"] + 5
        delta_after_status["balance"] == delta_before_status["balance"]
        epsilon_after_status["balance"] == epsilon_before_status["balance"]
        zeta_after_status["balance"] == zeta_before_status["balance"]


if __name__ == "__main__":
    unittest.main()
