import os
import subprocess
import unittest
import uuid

from testwithbaton._common import create_client
from testwithbaton._irods_server import create_irods_test_server, start_irods
from testwithbaton.api import TestWithBatonSetup, IrodsEnvironmentKey, get_irods_server_from_environment_if_defined
from testwithbaton.helpers import SetupHelper
from testwithbaton.models import BatonDockerBuild


class TestTestWithBatonSetup(unittest.TestCase):
    """
    Unit tests for `TestWithBatonSetup`.
    """
    def setUp(self):
        self.test_with_baton = TestWithBatonSetup()
        self.test_with_baton.setup()
        self.setup_helper = SetupHelper(self.test_with_baton.icommands_location)

    def test_can_use_icommand_binary(self):
        self.assertEquals(self.setup_helper.run_icommand("ils"),
                          "/iplant/home/%s:" % self.test_with_baton.irods_test_server.users[0].username)

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
        for line in ienv_output.split('\n'):
            if "irodsPort" in line:
                port = int(line.split('=')[1])
                break
        assert port != -1

        self.assertEquals(port, irods_server.port)

    def test_can_use_custom_baton_docker(self):
        external_unique_identifier = str(uuid.uuid4())
        custom_baton_docker_build = BatonDockerBuild(
            "github.com/wtsi-hgi/docker-baton.git",
            "wtsi-hgi/baton/tests:%s-%s" % (self._testMethodName, external_unique_identifier),
            "custom/irods-3.3.1/Dockerfile",
            {
                "REPOSITORY": "https://github.com/wtsi-npg/baton.git",
                "BRANCH": "release-0.16.1"
            }
        )

        test_with_baton_with_custom_baton_docker = TestWithBatonSetup(baton_docker_build=custom_baton_docker_build)
        test_with_baton_with_custom_baton_docker.setup()

        client = create_client()
        tags = []
        for image in client.images():
            tags.extend(image["RepoTags"])
        self.assertIn(custom_baton_docker_build.build_name, tags)

        test_with_baton_with_custom_baton_docker.tear_down()
        client.remove_image(custom_baton_docker_build.build_name, force=True, noprune=True)

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
        self.assertEquals(irods_server.host, TestGetIrodsServerFromEnvironmentIfDefined.HOST)
        self.assertEquals(irods_server.port, int(TestGetIrodsServerFromEnvironmentIfDefined.PORT))
        self.assertEquals(irods_server.users[0].username, TestGetIrodsServerFromEnvironmentIfDefined.USERNAME)
        self.assertEquals(irods_server.users[0].password, TestGetIrodsServerFromEnvironmentIfDefined.PASSWORD)
        self.assertEquals(irods_server.users[0].zone, TestGetIrodsServerFromEnvironmentIfDefined.ZONE)

    def tearDown(self):
        TestGetIrodsServerFromEnvironmentIfDefined._clean_environment()

    @staticmethod
    def _clean_environment():
        for key in IrodsEnvironmentKey:
            value = os.environ.get(key.value)
            if value is not None:
                del os.environ[key.value]


if __name__ == "__main__":
    unittest.main()
