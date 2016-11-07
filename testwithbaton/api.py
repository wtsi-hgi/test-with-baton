import atexit
import logging
import os
from enum import Enum, unique
from typing import Union

from hgicommon.docker.client import create_client
from testwithbaton._baton import build_baton_docker
from testwithbaton.models import BatonImage
from testwithbaton.proxies import BatonProxyController
from testwithirods.api import IrodsVersion, get_static_irods_server_controller
from testwithirods.models import IrodsServer, IrodsUser
from testwithirods.proxies import ICommandProxyController


@unique
class BatonSetup(Enum):
    v0_16_1_WITH_IRODS_3_3_1 = (BatonImage("mercury/baton:0.16.1-with-irods-3.3.1"), IrodsVersion.v3_3_1)
    v0_16_2_WITH_IRODS_3_3_1 = (BatonImage("mercury/baton:0.16.2-with-irods-3.3.1"), IrodsVersion.v3_3_1)
    v0_16_2_WITH_IRODS_4_1_8 = (BatonImage("mercury/baton:0.16.2-with-irods-4.1.8"), IrodsVersion.v4_1_8)
    v0_16_3_WITH_IRODS_3_3_1 = (BatonImage("mercury/baton:0.16.3-with-irods-3.3.1"), IrodsVersion.v3_3_1)
    v0_16_3_WITH_IRODS_4_1_8 = (BatonImage("mercury/baton:0.16.3-with-irods-4.1.8"), IrodsVersion.v4_1_8)
    v0_16_4_WITH_IRODS_3_3_1 = (BatonImage("mercury/baton:0.16.4-with-irods-3.3.1"), IrodsVersion.v3_3_1)
    v0_16_4_WITH_IRODS_4_1_8 = (BatonImage("mercury/baton:0.16.4-with-irods-4.1.8"), IrodsVersion.v4_1_8)
    v0_16_4_WITH_IRODS_4_1_9 = (BatonImage("mercury/baton:0.16.4-with-irods-4.1.9"), IrodsVersion.v4_1_9)
    v0_17_0_WITH_IRODS_4_1_9 = (BatonImage("mercury/baton:0.17.0-with-irods-4.1.9"), IrodsVersion.v4_1_9)
    v0_17_0_WITH_IRODS_4_1_10 = (BatonImage("mercury/baton:0.17.0-with-irods-4.1.10"), IrodsVersion.v4_1_10)

LATEST_BATON_IMAGE_WITH_IRODS_3 = BatonSetup.v0_16_4_WITH_IRODS_3_3_1
LATEST_BATON_IMAGE_WITH_IRODS_4 = BatonSetup.v0_17_0_WITH_IRODS_4_1_10
DEFAULT_BATON_SETUP = LATEST_BATON_IMAGE_WITH_IRODS_4


class IrodsEnvironmentKey(Enum):
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
    for key in IrodsEnvironmentKey:
        environment_value = os.environ.get(key.value)
        if environment_value is None:
            return None

    return IrodsServer(
        os.environ[IrodsEnvironmentKey.IRODS_HOST.value],
        int(os.environ[IrodsEnvironmentKey.IRODS_PORT.value]),
        [IrodsUser(os.environ[IrodsEnvironmentKey.IRODS_USERNAME.value],
                   os.environ[IrodsEnvironmentKey.IRODS_ZONE.value],
                   os.environ[IrodsEnvironmentKey.IRODS_PASSWORD.value])]
    )


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

    def __init__(self, baton_image: BatonImage=DEFAULT_BATON_SETUP.value[0],
                 irods_version_to_start: IrodsVersion=DEFAULT_BATON_SETUP.value[1], irods_server: IrodsServer=None,
                 baton_setup: BatonSetup=None):
        """
        Constructor.
        :param baton_image: baton Docker image that is to be used
        :param irods_version_to_start: the version of iRODS to start (if any)
        :param irods_server: the started iRODS server ot use (if any)
        :param baton_setup: the baton setup to use (if any)
        """
        if baton_setup is not None:
            baton_image = baton_setup.value[0]
            irods_version_to_start = baton_setup.value[1]
        if irods_version_to_start is None and irods_server is None:
            raise ValueError("Must either define an iRODs server to use or a version of iRODS that is to be started")
        if irods_version_to_start is not None and irods_server is not None:
            raise ValueError("Must either define an iRODs server to use or a version of iRODS to start, not both")

        # Ensure that no matter what happens, tear down is done
        atexit.register(self.tear_down)

        self.irods_server = irods_server
        self._irods_version_to_start = irods_version_to_start
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
            # baton Docker image is to be built from a local Dockerfile
            logging.debug("Building baton Docker")
            build_baton_docker(docker_client, self._baton_docker_build)
        else:
            # Ensuring Docker image is pulled - not waiting until `docker run` to prevent Docker from polluting the
            # stderr
            if ":" in self._baton_docker_build.tag:
                repository, tag = self._baton_docker_build.tag.split(":")
            else:
                repository = self._baton_docker_build.tag
                tag = ""

            docker_image = docker_client.images("%s:%s" % (repository, tag), quiet=True)
            if len(docker_image) == 0:
                # Docker image doesn't exist locally: getting from DockerHub
                docker_client.pull(repository, tag)

        if self._irods_version_to_start:
            logging.debug("Starting iRODS test server")
            self.irods_server = get_static_irods_server_controller(self._irods_version_to_start).start_server()
            logging.debug("iRODS test server has started")
        else:
            logging.debug("Using pre-existing iRODS server")

        self._setup_proxies()

        logging.debug("Setup complete")

    def _setup_proxies(self):
        logging.debug("Creating proxies")
        self._baton_binary_proxy_controller = BatonProxyController(self.irods_server, self._baton_docker_build.tag)
        self.baton_location = self._baton_binary_proxy_controller.create_proxy_binaries()

        self._icommand_binary_proxy_controller = ICommandProxyController(
            self.irods_server, self._baton_docker_build.tag)
        # Make icommand proxy binaries share cached container with baton proxy binaries to get a speedup
        self._icommand_binary_proxy_controller.cached_container_name = self._baton_binary_proxy_controller.cached_container_name
        self.icommands_location = self._icommand_binary_proxy_controller.create_proxy_binaries()

    def tear_down(self):
        """
        Tear down the test environment.
        """
        if self._state == TestWithBaton._SetupState.RUNNING:
            self._state = TestWithBaton._SetupState.STOPPED
            atexit.unregister(self.tear_down)

            if self._irods_version_to_start is not None:
                logging.debug("Stopping iRODS server")
                get_static_irods_server_controller(self._irods_version_to_start).stop_server(self.irods_server)
                self.irods_server = None
            else:
                logging.debug("External iRODS test server used - not tearing down")

            logging.debug("Tearing down binary proxies")
            self._tear_down_proxies()
            self.baton_location = None
            self.icommands_location = None

            logging.debug("Tear down complete")

    def _tear_down_proxies(self):
        """
        Tears down the baton and icommand proxy binaries.
        """
        if self._baton_binary_proxy_controller is not None:
            self._baton_binary_proxy_controller.tear_down()
        if self._icommand_binary_proxy_controller is not None:
            self._icommand_binary_proxy_controller.tear_down()
