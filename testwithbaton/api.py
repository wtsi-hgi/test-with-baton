import atexit
import logging
import os
from enum import Enum, unique
from typing import Union

from testwithbaton._baton import build_baton_docker
from testwithbaton._common import create_client
from testwithbaton._proxies import BatonProxyController, ICommandProxyController
from testwithbaton.irods import get_irods_server_controller, IrodsVersion
from testwithbaton.models import IrodsServer, IrodsUser, BatonImage

@unique
class BatonSetup(Enum):
    v0_16_1_WITH_IRODS_3_3_1 = (BatonImage("mercury/baton:0.16.1-with-irods-3.3.1"), IrodsVersion.v3_3_1)
    v0_16_2_WITH_IRODS_3_3_1 = (BatonImage("mercury/baton:0.16.2-with-irods-3.3.1"), IrodsVersion.v3_3_1)
    v0_16_2_WITH_IRODS_4_1_8 = (BatonImage("mercury/baton:0.16.2-with-irods-4.1.8"), IrodsVersion.v4_1_8)

LATEST_BATON_IMAGE_WITH_IRODS_3 = BatonSetup.v0_16_2_WITH_IRODS_3_3_1
LATEST_BATON_IMAGE_WITH_IRODS_4 = BatonSetup.v0_16_2_WITH_IRODS_4_1_8
DEFAULT_BATON_SETUP = LATEST_BATON_IMAGE_WITH_IRODS_3


# class IrodsEnvironmentKey(Enum):
#     """
#     Keys of environment variables that may be used to define an iRODS server that can be loaded using
#     `get_irods_server_from_environment_if_defined`.
#     """
#     IRODS_HOST = "IRODS_HOST"
#     IRODS_PORT = "IRODS_PORT"
#     IRODS_USERNAME = "IRODS_USERNAME"
#     IRODS_PASSWORD = "IRODS_PASSWORD"
#     IRODS_ZONE = "IRODS_ZONE"
#
#
# def get_irods_server_from_environment_if_defined() -> Union[None, IrodsServer]:
#     """
#     Instantiates an iRODS server that has been defined through environment variables. If no definition/an incomplete
#     definition was found, returns `None`.
#     :return: a representation of the iRODS server defined through environment variables else `None` if no definition
#     """
#     for key in IrodsEnvironmentKey:
#         environment_value = os.environ.get(key.value)
#         if environment_value is None:
#             return None
#
#     return IrodsServer(
#         os.environ[IrodsEnvironmentKey.IRODS_HOST.value],
#         int(os.environ[IrodsEnvironmentKey.IRODS_PORT.value]),
#         [IrodsUser(os.environ[IrodsEnvironmentKey.IRODS_USERNAME.value],
#                    os.environ[IrodsEnvironmentKey.IRODS_ZONE.value],
#                    os.environ[IrodsEnvironmentKey.IRODS_PASSWORD.value])]
#     )


class TestWithBaton:
    """
    A setup for testing with baton.
    """
    @unique
    class _SetupState(Enum):
        """
        States of a `TestWithBaton` instance.
        """
        INIT = 0,
        RUNNING = 1,
        STOPPED = 2

    def __init__(self, irods_server: IrodsServer=None, baton_image: BatonImage=DEFAULT_BATON_SETUP.value[0]):
        """
        Constructor.
        :param irods_server: a pre-configured, running iRODS server to use in the tests
        :param baton_image: baton Docker image that is to be used
        """
        # Ensure that no matter what happens, tear down is done
        atexit.register(self.tear_down)

        self.irods_server = irods_server
        self._external_irods_server = irods_server is not None
        self._state = TestWithBaton._SetupState.INIT
        self._baton_docker_build = baton_image

        self.baton_location = None
        self.icommands_location = None

        self._baton_binary_proxy_controller = None  # type: BatonProxyController
        self._icommand_binary_proxy_controller = None  # type: ICommandProxyController

    def setup(self):
        """
        Sets up the setup: builds the baton Docker image, starts the iRODS test server (if required) and creates the
        proxies.
        """
        if self._state != TestWithBaton._SetupState.INIT:
            raise RuntimeError("Already been setup")
        self._state = TestWithBaton._SetupState.RUNNING

        docker_client = create_client()
        if self._baton_docker_build.docker_file is not None:
            # baton Docker image is not in Docker Hub
            logging.debug("Building baton Docker")
            build_baton_docker(docker_client, self._baton_docker_build)
        else:
            # Pull Docker image from Docker Hub - not waiting until `docker run` to prevent Docker from polluting the
            # stderr
            if ":" in self._baton_docker_build.tag:
                repository, tag = self._baton_docker_build.tag.split(":")
            else:
                repository = self._baton_docker_build.tag
                tag = None
            docker_client.pull(repository, tag)

        if not self._external_irods_server:
            logging.debug("Starting iRODS test server")
            # FIXME: Issue here!
            self.irods_server = get_irods_server_controller().start_server()
            logging.debug("iRODS test server has started")
        else:
            logging.debug("Using pre-existing iRODS server")

        self._setup_proxies()
        logging.debug("Setup complete")

    def _setup_proxies(self):
        logging.debug("Creating proxies")
        self._baton_binary_proxy_controller = BatonProxyController(
            self.irods_server, self._baton_docker_build.tag)
        self.baton_location = self._baton_binary_proxy_controller.create_proxy_binaries()

        self._icommand_binary_proxy_controller = ICommandProxyController(
            self.irods_server, self._baton_docker_build.tag)
        self.icommands_location = self._icommand_binary_proxy_controller.create_proxy_binaries()

    def tear_down(self):
        """
        Tear down the test environment.
        """
        if self._state == TestWithBaton._SetupState.RUNNING:
            self._state = TestWithBaton._SetupState.STOPPED
            atexit.unregister(self.tear_down)

            if not self._external_irods_server:
                self._tear_down_irods_test_server()
            else:
                logging.debug("External iRODS test server used - not tearing down")

            logging.debug("Tearing down binary proxies")
            self._tear_down_proxies()
            self.baton_location = None
            self.icommands_location = None

            logging.debug("Tear down complete")

    def _tear_down_proxies(self):
        """
        TODO
        """
        if self._baton_binary_proxy_controller is not None:
            self._baton_binary_proxy_controller.tear_down()
        if self._icommand_binary_proxy_controller is not None:
            self._icommand_binary_proxy_controller.tear_down()

    def _tear_down_irods_test_server(self):
        """
        Tears down the iRODS test server.
        """
        assert not self._external_irods_server
        logging.debug("Killing iRODS test server")
        docker_client = create_client()
        try:
            if self.irods_server is not None:
                docker_client.kill(self.irods_server.native_object)
        except Exception as error:
            logging.error(error)
        self.irods_server = None
