import atexit
import logging
import os
import shutil
from enum import Enum, unique
from typing import Union

from testwithbaton.common import create_client
from testwithbaton.irods_server import create_irods_test_server, start_irods
from irodscommon.models import IrodsServer, IrodsUser
from testwithbaton.proxies import build_baton_docker, create_baton_proxy_binaries, create_icommands_proxy_binaries


class irodsEnvironmentKey(Enum):
    """
    Keys of environment variables that may be used to define an iRODS server that can be loaded using
    `get_irods_server_from_environment_if_defined`.
    """
    IRODS_HOST = "IRODS_HOST"
    IRODS_PORT = "IRODS_PORT"
    IRODS_USERNAME = "IRODS_USERNAME"
    IRODS_PASSWORD = "IRODS_PASSWORD"
    IRODS_ZONE = "IRODS_ZONE"


def get_irods_server_from_environment_if_defined() -> Union[None, IrodsServer]:
    """
    Instantiates an iRODS server that has been defined through environment variables. If no definition/an incomplete
    definition was found, returns `None`.
    :return: a representation of the iRODS server defined through environment variables else `None` if no definition
    """
    for key in irodsEnvironmentKey:
        environmentValue = os.environ.get(key.value)
        if environmentValue is None:
            return None

    return IrodsServer(
        os.environ[irodsEnvironmentKey.IRODS_HOST.value],
        int(os.environ[irodsEnvironmentKey.IRODS_PORT.value]),
        [IrodsUser(
            os.environ[irodsEnvironmentKey.IRODS_USERNAME.value],
            os.environ[irodsEnvironmentKey.IRODS_PASSWORD.value],
            os.environ[irodsEnvironmentKey.IRODS_ZONE.value],
        )]
    )


class TestWithBatonSetup:
    """
    A setup for testing with baton.
    """
    @unique
    class _SetupState(Enum):
        """
        States of a `TestWithBatonSetup` instance.
        """
        INIT = 0,
        RUNNING = 1,
        STOPPED = 2

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
        self._state = TestWithBatonSetup._SetupState.INIT

    def setup(self):
        if self._state != TestWithBatonSetup._SetupState.INIT:
            raise RuntimeError("Already been setup")
        self._state = TestWithBatonSetup._SetupState.RUNNING

        # Build baton Docker
        docker_client = create_client()
        logging.debug("Building baton Docker")
        build_baton_docker(docker_client)

        if not self._external_irods_test_server:
            logging.debug("Creating iRODS test server")
            self.irods_test_server = create_irods_test_server(docker_client)
            logging.debug("Starting iRODS test server")
            start_irods(docker_client, self.irods_test_server)
        else:
            logging.debug("Using pre-existing iRODS server")

        logging.debug("Creating proxies")
        self.baton_location = create_baton_proxy_binaries(self.irods_test_server)
        self.icommands_location = create_icommands_proxy_binaries(self.irods_test_server)
        logging.debug("Setup complete")

    def tear_down(self):
        """
        Tear down the test environment.
        """
        if self._state == TestWithBatonSetup._SetupState.RUNNING:
            self._state = TestWithBatonSetup._SetupState.STOPPED
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
