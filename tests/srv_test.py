import os
import shutil
import unittest
import tempfile
from picopayments_hub import srv
from picopayments_hub import __version__


class TestSRV(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="picopayments_test_")
        self.basedir = os.path.join(self.tempdir, "basedir")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_version(self):
        version = srv.main([
            "--basedir={0}".format(self.basedir),
            "--version"
        ], serve=False)
        self.assertEqual(version, __version__)

    def test_serve(self):
        pass  # FIXME implement test

        # func = request.environ.get('werkzeug.server.shutdown')
        # if func is None:
        #     raise RuntimeError('Not running with the Werkzeug Server')
        # raise RuntimeError('Running Werkzeug Server')
        # func()

        # def func():
        #     while True:
        #         time.sleep(1)
        #
        # thread = threading.Thread(target=func)
        # thread.start()
        #
        # time.sleep(10)
        #
        # if not 'werkzeug.server.shutdown' in environ:
        #     raise RuntimeError('Not running the development server')
        # environ['werkzeug.server.shutdown']()


if __name__ == "__main__":
    unittest.main()
