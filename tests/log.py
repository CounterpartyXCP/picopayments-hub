import os
import json
import shutil
import unittest
import tempfile
from picopayments import srv
from picopayments import rpc
from picopayments import log


rpc.CALL_LOCAL_PROCESS = True
CP_URL = "http://139.59.214.74:14000/api/"


class TestLog(unittest.TestCase):

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

    def tests_log(self):
        log.debug("test debug coverage")
        log.info("test info coverage")
        log.warn("test warn coverage")
        log.error("test error coverage")
        log.critical("test critical coverage")
        log.fatal("test fatal coverage")


if __name__ == "__main__":
    unittest.main()
