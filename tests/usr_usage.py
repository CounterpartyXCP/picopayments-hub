import os
import json
import shutil
import unittest
import tempfile
from picopayments import etc
from picopayments import srv
from picopayments_client.usr import HubClient
from tests.mock import MockAPI


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
        _c = self.data["connections"]

        # setup
        alpha = HubClient.deserialize(data=_c["alpha"], api_cls=MockAPI)
        beta = HubClient.deserialize(data=_c["beta"], api_cls=MockAPI)
        gamma = HubClient.deserialize(data=_c["gamma"], api_cls=MockAPI)
        delta = HubClient.deserialize(data=_c["delta"], api_cls=MockAPI)
        epsilon = HubClient.deserialize(data=_c["epsilon"], api_cls=MockAPI)
        zeta = HubClient.deserialize(data=_c["zeta"], api_cls=MockAPI)

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

        # sand more back so commits are revoked to maximize liquidity
        beta.micro_send(alpha.handle, 42, "0003")
        self.assertEqual(beta.sync(), [])
        self.assertEqual(alpha.sync(), [{
            "payer_handle": beta.handle,
            "amount": 42,
            "token": "0003"
        }])

        # get after status
        alpha_after_status = alpha.get_status()
        beta_after_status = beta.get_status()
        gamma_after_status = gamma.get_status()
        delta_after_status = delta.get_status()
        epsilon_after_status = epsilon.get_status()
        zeta_after_status = zeta.get_status()

        # compare statuses
        alpha_after_status["balance"] == alpha_before_status["balance"] + 29
        beta_after_status["balance"] == beta_before_status["balance"] - 39
        gamma_after_status["balance"] == gamma_before_status["balance"] + 5
        delta_after_status["balance"] == delta_before_status["balance"]
        epsilon_after_status["balance"] == epsilon_before_status["balance"]
        zeta_after_status["balance"] == zeta_before_status["balance"]

        alpha.update(dryrun=True)
        beta.update(dryrun=True)
        gamma.update(dryrun=True)
        delta.update(dryrun=True)
        epsilon.update(dryrun=True)
        zeta.update(dryrun=True)

        alpha.close(dryrun=True)
        beta.close(dryrun=True)
        gamma.close(dryrun=True)
        delta.close(dryrun=True)
        epsilon.close(dryrun=True)
        zeta.close(dryrun=True)


if __name__ == "__main__":
    unittest.main()
