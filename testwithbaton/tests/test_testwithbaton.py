import os
import subprocess
import unittest

from testwithbaton.helpers import SetupHelper

from testwithbaton.common import create_client

from testwithbaton.irods_server import create_irods_test_server, start_irods

from testwithbaton.api import TestWithBatonSetup


class TestPackage(unittest.TestCase):
    """
    System tests for testwithbaton package.
    """
    def setUp(self):
        self.test_with_baton = TestWithBatonSetup()
        self.test_with_baton.setup()
        self.setup_helper = SetupHelper(self.test_with_baton.icommands_location)

    def test_can_use_icommand_binary(self):
        self.assertEquals(self.setup_helper.run_icommand("ils"), "/iplant/home/testuser:")

    def test_can_use_baton_binary(self):
        process = subprocess.Popen(["%s/baton" % self.test_with_baton.baton_location],
                                   stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = process.communicate()

        self.assertEquals(str.strip(out.decode("utf-8")), "{\"avus\":[]}")
        self.assertEquals(error, None)

    def test_tear_down(self):
        baton_location = self.test_with_baton.baton_location
        icommands_location = self.test_with_baton.icommands_location

        self.test_with_baton.tear_down()

        self.assertFalse(os.path.exists(baton_location))
        self.assertFalse(os.path.exists(icommands_location))
        self.assertIsNone(self.test_with_baton.baton_location)
        self.assertIsNone(self.test_with_baton.icommands_location)

    def test_cannot_setup_again_after_tear_down(self):
        self.test_with_baton.tear_down()
        self.assertRaises(RuntimeError, self.test_with_baton.setup)

    def test_can_use_external_irods_server(self):
        docker_client = create_client()
        irods_server = create_irods_test_server(docker_client)
        start_irods(docker_client, irods_server)

        self.test_with_baton = TestWithBatonSetup(irods_server)
        self.test_with_baton.setup()
        self.setup_helper = SetupHelper(self.test_with_baton.icommands_location)

        ienv_output = self.setup_helper.run_icommand("ienv")

        port = -1
        for line in ienv_output.split("\n"):
            if "irodsPort" in line:
                port = int(line.split("=")[1])
                break
        assert port != -1

        self.assertEquals(port, irods_server.port)

    def tearDown(self):
        self.test_with_baton.tear_down()

if __name__ == '__main__':
    unittest.main()
