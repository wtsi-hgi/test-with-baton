import os
import subprocess
import unittest
from abc import ABCMeta

import testwithbaton
from testwithbaton.api import TestWithBaton, get_irods_server_from_environment_if_defined, IrodsEnvironmentKey
from testwithbaton.tests._common import BatonSetupContainer, create_tests_for_all_baton_setups
from testwithirods.helpers import SetupHelper


class TestTestWithBaton(unittest.TestCase, BatonSetupContainer, metaclass=ABCMeta):
    """
    Unit tests for `TestWithBaton`.
    """
    def setUp(self):
        self.test_with_baton = TestWithBaton(self.baton_setup.value[0], self.baton_setup.value[1])
        self.test_with_baton.setup()
        self.setup_helper = SetupHelper(self.test_with_baton.icommands_location)

    def tearDown(self):
        self.test_with_baton.tear_down()

    def test_can_use_icommand_binary(self):
        user = self.test_with_baton.irods_server.users[0]
        zone = user.zone
        username = user.username
        self.assertEquals(self.setup_helper.run_icommand(["ils"]), "/%s/home/%s:" % (zone, username))

    def test_can_use_baton_binary(self):
        process = subprocess.Popen(["%s/baton" % self.test_with_baton.baton_location],
                                   stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=None)
        out, error = process.communicate()

        self.assertEqual(str.strip(out.decode("utf-8")), "{\"avus\":[]}")
        self.assertEqual(error, None)

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


# Create tests for all baton versions
create_tests_for_all_baton_setups(TestTestWithBaton)
for name, value in testwithbaton.tests._common.__dict__.items():
    if TestTestWithBaton.__name__ in name:
        globals()[name] = value
del TestTestWithBaton


class TestGetIrodsServerFromEnvironmentIfDefined(unittest.TestCase):
    """
    Unit tests for `get_irods_server_from_environment_if_defined`.
    """
    HOST = "HOST"
    PORT = "123"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    ZONE = "ZONE"

    @staticmethod
    def _clean_environment():
        for key in IrodsEnvironmentKey:
            value = os.environ.get(key.value)
            if value is not None:
                del os.environ[key.value]

    def setUp(self):
        TestGetIrodsServerFromEnvironmentIfDefined._clean_environment()

    def tearDown(self):
        TestGetIrodsServerFromEnvironmentIfDefined._clean_environment()

    def test_none_if_not_defined(self):
        self.assertIsNone(get_irods_server_from_environment_if_defined())

    def test_none_if_partially_defined(self):
        os.environ[IrodsEnvironmentKey.IRODS_HOST.value] = TestGetIrodsServerFromEnvironmentIfDefined.HOST
        os.environ[IrodsEnvironmentKey.IRODS_USERNAME.value] = TestGetIrodsServerFromEnvironmentIfDefined.USERNAME
        self.assertIsNone(get_irods_server_from_environment_if_defined())

    def test_can_get_if_defined(self):
        os.environ[IrodsEnvironmentKey.IRODS_HOST.value] = TestGetIrodsServerFromEnvironmentIfDefined.HOST
        os.environ[IrodsEnvironmentKey.IRODS_PORT.value] = TestGetIrodsServerFromEnvironmentIfDefined.PORT
        os.environ[IrodsEnvironmentKey.IRODS_USERNAME.value] = TestGetIrodsServerFromEnvironmentIfDefined.USERNAME
        os.environ[IrodsEnvironmentKey.IRODS_PASSWORD.value] = TestGetIrodsServerFromEnvironmentIfDefined.PASSWORD
        os.environ[IrodsEnvironmentKey.IRODS_ZONE.value] = TestGetIrodsServerFromEnvironmentIfDefined.ZONE

        irods_server = get_irods_server_from_environment_if_defined()
        self.assertEqual(irods_server.host, TestGetIrodsServerFromEnvironmentIfDefined.HOST)
        self.assertEqual(irods_server.port, int(TestGetIrodsServerFromEnvironmentIfDefined.PORT))
        self.assertEqual(irods_server.users[0].username, TestGetIrodsServerFromEnvironmentIfDefined.USERNAME)
        self.assertEqual(irods_server.users[0].password, TestGetIrodsServerFromEnvironmentIfDefined.PASSWORD)
        self.assertEqual(irods_server.users[0].zone, TestGetIrodsServerFromEnvironmentIfDefined.ZONE)


if __name__ == "__main__":
    unittest.main()
