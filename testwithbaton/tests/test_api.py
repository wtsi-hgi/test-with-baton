import os
import subprocess
import unittest

from testwithbaton.helpers import SetupHelper

from testwithbaton.common import create_client

from testwithbaton.irods_server import create_irods_test_server, start_irods

from testwithbaton.api import TestWithBatonSetup, irodsEnvironmentKey, get_irods_server_from_environment_if_defined


class TestTestWithBatonSetup(unittest.TestCase):
    """
    Unit tests for `TestWithBatonSetup`.
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

    def test_cannot_setup_if_already_setup(self):
        self.assertRaises(RuntimeError, self.test_with_baton.setup)

    def test_cannot_setup_after_tear_down(self):
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


class TestGetIrodsServerFromEnvironmentIfDefined(unittest.TestCase):
    """
    Unit tests for `get_irods_server_from_environment_if_defined`.
    """
    HOST = "HOST"
    PORT = "123"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    ZONE = "ZONE"

    def setUp(self):
        TestGetIrodsServerFromEnvironmentIfDefined._clean_environment()

    def test_none_if_not_defined(self):
        self.assertIsNone(get_irods_server_from_environment_if_defined())

    def test_none_if_partially_defined(self):
        os.environ[irodsEnvironmentKey.IRODS_HOST.value] = TestGetIrodsServerFromEnvironmentIfDefined.HOST
        os.environ[irodsEnvironmentKey.IRODS_USERNAME.value] = TestGetIrodsServerFromEnvironmentIfDefined.USERNAME
        self.assertIsNone(get_irods_server_from_environment_if_defined())

    def test_can_get_if_defined(self):
        os.environ[irodsEnvironmentKey.IRODS_HOST.value] = TestGetIrodsServerFromEnvironmentIfDefined.HOST
        os.environ[irodsEnvironmentKey.IRODS_PORT.value] = TestGetIrodsServerFromEnvironmentIfDefined.PORT
        os.environ[irodsEnvironmentKey.IRODS_USERNAME.value] = TestGetIrodsServerFromEnvironmentIfDefined.USERNAME
        os.environ[irodsEnvironmentKey.IRODS_PASSWORD.value] = TestGetIrodsServerFromEnvironmentIfDefined.PASSWORD
        os.environ[irodsEnvironmentKey.IRODS_ZONE.value] = TestGetIrodsServerFromEnvironmentIfDefined.ZONE

        irods_server = get_irods_server_from_environment_if_defined()
        self.assertEquals(irods_server.host, TestGetIrodsServerFromEnvironmentIfDefined.HOST)
        self.assertEquals(irods_server.port, int(TestGetIrodsServerFromEnvironmentIfDefined.PORT))
        self.assertEquals(irods_server.users[0].username, TestGetIrodsServerFromEnvironmentIfDefined.USERNAME)
        self.assertEquals(irods_server.users[0].password, TestGetIrodsServerFromEnvironmentIfDefined.PASSWORD)
        self.assertEquals(irods_server.users[0].zone, TestGetIrodsServerFromEnvironmentIfDefined.ZONE)

    def tearDown(self):
        TestGetIrodsServerFromEnvironmentIfDefined._clean_environment()

    @staticmethod
    def _clean_environment():
        for key in irodsEnvironmentKey:
            value = os.environ.get(key.value)
            if value is not None:
                del os.environ[key.value]


if __name__ == '__main__':
    unittest.main()
