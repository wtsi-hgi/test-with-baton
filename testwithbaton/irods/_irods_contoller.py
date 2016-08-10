import atexit
import logging
import os
import tempfile
from abc import abstractmethod, ABCMeta
from typing import Sequence

from testwithbaton._common import create_unique_name, create_client
from testwithbaton.models import ContainerisedIrodsServer, IrodsServer, IrodsUser, Version


class StaticIrodsServerController():
    """
    Static iRODS server controller.
    """
    @staticmethod
    @abstractmethod
    def start_server() -> ContainerisedIrodsServer:
        """
        Starts a containerised iRODS server and blocks until it is ready to be used.
        :return: the started containerised iRODS server
        """

    @staticmethod
    @abstractmethod
    def stop_server(container: ContainerisedIrodsServer):
        """
        Stops the given containerised iRODS server.
        :param container: the containerised iRODS server to stop
        """

    @staticmethod
    @abstractmethod
    def write_connection_settings(file_location: str, irods_server: IrodsServer):
        """
        Writes the connection settings for the given iRODS server to the given location.
        :param file_location: the location to write the settings to (file should not already exist)
        :param irods_server: the iRODS server to create the connection settings for
        """


class IrodsServerController(metaclass=ABCMeta):
    """
    Controller for containerised iRODS servers.
    """
    _DOCKER_CLIENT = create_client()
    _DEFAULT_IRODS_PORT = 1247

    @staticmethod
    def _create_container(image_name: str, irods_version: Version, users: Sequence[IrodsUser]) \
            -> ContainerisedIrodsServer:
        """
        Creates a iRODS server container running the given image. Will used a cached version of the image if available.
        :param image_name: the image to run
        :param irods_version: version of iRODS
        :param users: the iRODS users
        :return: the containerised iRODS server
        """
        cached_image_name = IrodsServerController._cached_image_name(image_name)
        docker_image = IrodsServerController._DOCKER_CLIENT.images(cached_image_name, quiet=True)

        if len(docker_image) == 0:
            docker_image = image_name
            # Note: Unlike with Docker cli, docker-py does not appear to search for images on Docker Hub if they are not
            # found when building
            logging.info("Pulling iRODs server Docker image: %s - this may take a few minutes" % docker_image)
            response = IrodsServerController._DOCKER_CLIENT.pull(docker_image)
            logging.debug(response)
        else:
            docker_image = docker_image[0]

        container_name = create_unique_name("irods")
        logging.info("Creating iRODs server Docker container: %s" % container_name)
        container = IrodsServerController._DOCKER_CLIENT.create_container(
            image=docker_image, name=container_name, ports=[IrodsServerController._DEFAULT_IRODS_PORT])

        irods_server = ContainerisedIrodsServer()
        irods_server.native_object = container
        irods_server.name = container_name
        irods_server.host = container_name
        irods_server.version = irods_version
        irods_server.users = users
        irods_server.port = IrodsServerController._DEFAULT_IRODS_PORT
        return irods_server

    @staticmethod
    def _cached_image_name(image_name: str) -> str:
        """
        Gets the corresponding image name for a cached version of an image with the given name.
        :param image_name: the image name to find corresponding cached image name for
        :return: the cached image name
        """
        return "%s-cached" % image_name

    @staticmethod
    def _cache_started_container(container: ContainerisedIrodsServer, image_name: str):
        """
        Caches the started container.
        :param container: the container to created cached image for
        :param image_name: the name of the image that is to be cached
        """
        cached_image_name = IrodsServerController._cached_image_name(image_name)
        if len(IrodsServerController._DOCKER_CLIENT.images(cached_image_name, quiet=True)) == 0:
            repository, tag = cached_image_name.split(":")
            IrodsServerController._DOCKER_CLIENT.commit(container.native_object["Id"], repository=repository, tag=tag)

    @abstractmethod
    def write_connection_settings(self, file_location: str, irods_server: IrodsServer):
        """
        Writes the connection settings for the given iRODS server to the given location.
        :param file_location: the location to write the settings to (file should not already exist)
        :param irods_server: the iRODS server to create the connection settings for
        """

    @abstractmethod
    def _wait_for_start(self, container: ContainerisedIrodsServer) -> bool:
        """
        Blocks until the given containerized iRODS server has started.
        :param container: the containerised server
        """

    @abstractmethod
    def start_server(self) -> ContainerisedIrodsServer:
        """
        Starts a containerised iRODS server and blocks until it is ready to be used.
        :return: the started containerised iRODS server
        """

    def stop_server(self, container: ContainerisedIrodsServer):
        """
        Stops the given containerised iRODS server.
        :param container: the containerised iRODS server to stop
        """
        try:
            if container is not None:
                IrodsServerController._DOCKER_CLIENT.kill(container.native_object)
        except Exception:
            # TODO: Should not use such a general exception
            pass

    def create_connection_settings_volume(self, config_file_name: str, irods_server: IrodsServer) -> str:
        """
        Creates a directory with iRODS config settings that can be used to supply the iRODS settings if mounted as a
        volume at `~/.irods`.
        :param config_file_name: the name of the configuration file to write
        :param irods_server: the iRODS server that is being connected to
        """
        temp_directory = tempfile.mkdtemp(prefix="irods-config-")
        logging.info("Created temp directory for iRODS config: %s" % temp_directory)

        connection_file = os.path.join(temp_directory, config_file_name)
        self.write_connection_settings(connection_file, irods_server)

        return temp_directory

    def _start_server(self, image_name: str, irods_version: Version, users: Sequence[IrodsUser]) \
            -> ContainerisedIrodsServer:
        """
        Starts a containerised iRODS server and blocks until it is ready to be used.
        :param image_name: the name of the iRODS server to start
        :param irods_version: the version of iRODS that is being started
        :param users: the users that have access to the started iRODS service
        :return: the started containerised iRODS server
        """
        logging.info("Starting iRODS server in Docker container")
        container = None
        started = False

        while not started:
            container = IrodsServerController._create_container(image_name, irods_version, users)
            atexit.register(self.stop_server, container)
            IrodsServerController._DOCKER_CLIENT.start(container.native_object)

            started = self._wait_for_start(container)
            if not started:
                logging.warning("iRODS server did not start correctly - restarting...")
                IrodsServerController._DOCKER_CLIENT.kill(container.native_object)
        assert container is not None

        IrodsServerController._cache_started_container(container, image_name)

        return container


def create_static_irods_server_controller(irods_server_controller: IrodsServerController) \
        -> StaticIrodsServerController:
    """
    Creates a static iRODS server controller from the given iRODS server controller. This essentially makes the given
    controller a singleton in a (static) sheep's clothing.
    :param irods_server_controller:
    :return:
    """
    static_controller = type(
        "%sFactory" % type(irods_server_controller).__name__.replace("Controller", ""),
        (StaticIrodsServerController,),
        dict()
    )
    static_controller.start_server = irods_server_controller.start_server
    static_controller.stop_server = irods_server_controller.stop_server
    static_controller.write_connection_settings = irods_server_controller.write_connection_settings
    return static_controller
