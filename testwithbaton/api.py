import atexit
import logging
import shutil
from enum import Enum, unique

from testwithbaton.common import create_client
from testwithbaton.irods_server import create_irods_test_server, start_irods
from testwithbaton.models import IrodsServer
from testwithbaton.proxies import build_baton_docker, create_baton_proxy_binaries, create_icommands_proxy_binaries


@unique
class _SetupState(Enum):
    """
    States of a `TestWithBatonSetup` instance.
    """
    INIT = 0,
    RUNNING = 1,
    STOPPED = 2


class TestWithBatonSetup:
    """
    A setup for testing with baton.
    """
    # TODO: Allow setting what irods test server to create if none given
    def __init__(self, irods_test_server: IrodsServer=None):
        """
        Default constructor.
        :param irods_test_server: a pre-configured, running iRODS server to use in the tests
        """
        # Ensure that no matter what happens, tear down is done
        atexit.register(self.tear_down)

        self.irods_test_server = irods_test_server
        self._external_irods_test_server = irods_test_server is not None
        self._state = _SetupState.INIT

    def setup(self):
        if self._state != _SetupState.INIT:
            raise RuntimeError("Already been setup")
        self._state = _SetupState.RUNNING

        # Build baton Docker
        docker_client = create_client()
        build_baton_docker(docker_client)

        if not self._external_irods_test_server:
            self.irods_test_server = create_irods_test_server(docker_client)
            start_irods(docker_client, self.irods_test_server)

        self.baton_location = create_baton_proxy_binaries(self.irods_test_server)
        self.icommands_location = create_icommands_proxy_binaries(self.irods_test_server)

    def tear_down(self):
        """
        Tear down the test environment.
        """
        if self._state == _SetupState.RUNNING:
            self._state = _SetupState.STOPPED
            atexit.unregister(self.tear_down)

            if not self._external_irods_test_server:
                self._tear_down_irods_test_server()
            else:
                logging.debug("External iRODS test server used - not tearing down")

            logging.debug("Removing temp folders")
            TestWithBatonSetup._tear_down_temp_directory(self.baton_location)
            TestWithBatonSetup._tear_down_temp_directory(self.icommands_location)
            self.baton_location = None
            self.icommands_location = None

            logging.debug("Tear down complete")

    def _tear_down_irods_test_server(self):
        """
        Tears down the iRODS test server.
        """
        assert not self._external_irods_test_server
        logging.debug("Killing iRODS test server")
        docker_client = create_client()
        try:
            docker_client.kill(self.irods_test_server.container)
        except Exception as error:
            logging.error(error)
        self.irods_test_server = None

    @staticmethod
    def _tear_down_temp_directory(directory: str):
        """
        Safely tears down the given temporary directory.
        :param directory: the directory to tear down
        """
        try:
            shutil.rmtree(directory)
        except Exception as error:
            logging.error(error)
