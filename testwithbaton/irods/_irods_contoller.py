import logging
import os
import tempfile
from abc import abstractmethod, ABCMeta, abstractstaticmethod
from typing import Optional, Sequence

from docker import Client

from testwithbaton._common import create_unique_name, create_client
from testwithbaton.models import ContainerisedIrodsServer, IrodsUser, IrodsServer


class IrodsServerController(metaclass=ABCMeta):
    """
    Controller for containerised iRODS servers.
    """
    @abstractmethod
    def start_server(self) -> ContainerisedIrodsServer:
        """
        Starts a containerised iRODS server and blocks until it is ready to be used.
        :return: the started containerised iRODS server
        """

    @abstractmethod
    def stop_server(self, container: ContainerisedIrodsServer):
        """
        Stops the containerised iRODS server.
        """

    @abstractstaticmethod
    def write_connection_settings(file_location: str, irods_server: IrodsServer):
        """
        Writes the connection settings for the given iRODS server to the given location.
        :param file_location: the location to write the settings to (file should not already exist)
        :param irods_server: the iRODS server to create the connection settings for
        """

    @staticmethod
    def _cached_image_name(image_name: str) -> str:
        """
        Gets the corresponding image name for a cached version of an image with the given name.
        :param image_name: the image name to find corresponding cached image name for
        :return: the cached image name
        """
        return "%s-cached" % image_name

    @staticmethod
    def create_connection_settings_volume(config_file_name: str, irods_server: IrodsServer) -> str:
        """
        TODO
        :param config_file_name:
        :param irods_server:
        """
        temp_directory = tempfile.mkdtemp(prefix="irods-config-")
        logging.info("Created temp directory for iRODS config: %s" % temp_directory)
        # os.chmod(temp_directory, 0o777)

        connection_file = os.path.join(temp_directory, config_file_name)
        IrodsServerController.write_connection_settings(connection_file, irods_server)

        return temp_directory

    def __init__(self):
        """
        Constructor.
        """
        self._docker_client = None  # type: Optional[Client]

    @property
    def docker_client(self) -> Client:
        """
        Docker client.
        :return: the Docker client
        """
        if self._docker_client is None:
            self._docker_client = create_client()
        return self._docker_client

    def _create_container(self, image_name: str, users: Sequence[IrodsUser]) -> ContainerisedIrodsServer:
        """
        Creates a iRODS server container running the given image.
        :param image_name: the image to run
        :param users: the iRODS users
        :return: the containerised iRODS server
        """
        cached_image_name = IrodsServerController._cached_image_name(image_name)
        docker_image = self.docker_client.images(cached_image_name, quiet=True)

        if len(docker_image) == 0:
            docker_image = image_name
            # Note: Unlike with Docker cli, docker-py does not appear to search for images on Docker Hub if they are not
            # found when building
            logging.info("Pulling iRODs server Docker image: %s - this may take a few minutes" % docker_image)
            response = self.docker_client.pull(docker_image)
            logging.debug(response)
        else:
            docker_image = docker_image[0]

        container_name = create_unique_name("irods")
        logging.info("Creating iRODs server Docker container: %s" % container_name)
        container = self.docker_client.create_container(image=docker_image, name=container_name, ports=[1247])

        irods_server = ContainerisedIrodsServer()
        irods_server.native_object = container
        irods_server.name = container_name
        irods_server.users = users
        return irods_server
