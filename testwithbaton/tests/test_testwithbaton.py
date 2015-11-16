import os
import string
import subprocess
import unittest

from testwithbaton.api import TestWithBatonSetup


class TestPackage(unittest.TestCase):
    """
    System tests for testwithbaton package.
    """
    def setUp(self):
        test_with_baton = TestWithBatonSetup()
        test_with_baton.setup()
        self._test_with_baton = test_with_baton

    def test_can_use_icommand_binary(self):
        process = subprocess.Popen(["%s/ils" % self._test_with_baton.icommands_location],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = process.communicate()

        self.assertEquals(TestPackage._output_to_string(out), "/iplant/home/testuser:")
        self.assertEquals(error, None)

    def test_can_use_baton_binary(self):
        process = subprocess.Popen(["%s/baton" % self._test_with_baton.baton_location],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = process.communicate()

        self.assertEquals(TestPackage._output_to_string(out), "{\"avus\":[]}")
        self.assertEquals(error, None)

    def test_tear_down(self):
        baton_location = self._test_with_baton.baton_location
        icommands_location = self._test_with_baton.icommands_location

        self._test_with_baton.tear_down()

        self.assertFalse(os.path.exists(baton_location))
        self.assertFalse(os.path.exists(icommands_location))
        self.assertIsNone(self._test_with_baton.baton_location)
        self.assertIsNone(self._test_with_baton.icommands_location)

    def test_can_setup_again_after_tear_down(self):
        self._test_with_baton.tear_down()
        self._test_with_baton.setup()

    def tearDown(self):
        self._test_with_baton.tear_down()

    @staticmethod
    def _output_to_string(output: bytes):
        return str.strip(output.decode("utf-8"))


if __name__ == '__main__':
    unittest.main()
