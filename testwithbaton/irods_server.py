import logging
import os
import tempfile
from typing import Tuple

from docker import Client
from irodscommon.models import IrodsServer, IrodsUser

from testwithbaton.common import create_unique_container_name, get_open_port, find_hostname
from testwithbaton.models import ContainerisedIrodsServer

_IRODS_CONFIG_FILE_NAME = ".irodsEnv"

# TODO: Should be settings
_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_ZONE_PARAMETER_NAME = "irodsZone"

_IRODS_TEST_SERVER_DOCKER = "agaveapi/irods:3.3.1"
_IRODS_TEST_SERVER_USERNAME = "testuser"
_IRODS_TEST_SERVER_PASSWORD = "testuser"
_IRODS_TEST_SERVER_ZONE = "iplant"


def create_irods_test_server(docker_client: Client) -> ContainerisedIrodsServer:
    """
    Creates an iRODS test server in a Docker container.
    :param docker_client: a Docker client
    :return: model of the created iRODS server
    """
    container, port = _create_irods_server_container(docker_client)
    hostname = find_hostname(docker_client)
    users = [IrodsUser(_IRODS_TEST_SERVER_USERNAME, _IRODS_TEST_SERVER_PASSWORD, _IRODS_TEST_SERVER_ZONE)]

    return ContainerisedIrodsServer(container, hostname, port, users)


def start_irods(docker_client: Client, irods_test_server: ContainerisedIrodsServer):
    """
    Starts iRODS server.
    :param docker_client: the Docker client used to start the server
    :param irods_test_server: the server setup
    """
    logging.info("Starting iRODS server in Docker container on PORT: %d" % irods_test_server.port)
    docker_client.start(irods_test_server.container)

    # Block until iRODS is setup
    logging.info("Waiting for iRODS server to have setup")
    for line in docker_client.logs(irods_test_server.container, stream=True):
        logging.debug(line)
        if "exited: irods" in str(line):
            break


def write_irods_server_connection_settings(write_settings_file_to: str, irods_server: IrodsServer):
    """
    Writes the connection settings for the given iRODS server to the given location.
    :param write_settings_file_to: the location to write the settings to (file should not already exist)
    :param irods_server: the iRODS server to create the connection settings for
    """
    if os.path.isfile(write_settings_file_to):
        raise ValueError("Settings cannot be written to a file that already exists")

    user = irods_server.users[0]
    config = [
        (_IRODS_USERNAME_PARAMETER_NAME, user.username),
        (_IRODS_HOST_PARAMETER_NAME, irods_server.host),
        (_IRODS_PORT_PARAMETER_NAME, irods_server.port),
        (_IRODS_ZONE_PARAMETER_NAME, user.zone)
    ]
    logging.debug("Writing iRODS connection config to: %s" % write_settings_file_to)
    settings_file = open(write_settings_file_to, 'w')
    settings_file.write('\n'.join(["%s %s" % x for x in config]))
    settings_file.close()


def create_irods_server_connection_settings_volume(irods_server: IrodsServer) -> str:
    """
    Creates a directory that contains the iRODS connection settings for the given server.
    :param irods_server:
    :return: the location of the "volume" (i.e. directory) containing the configuration
    """
    temp_directory = tempfile.mkdtemp(prefix="irods-config-")
    logging.info("Created temp directory for iRODS config: %s" % temp_directory)
    os.chmod(temp_directory, 0o777)

    connection_file = os.path.join(temp_directory, _IRODS_CONFIG_FILE_NAME)
    write_irods_server_connection_settings(connection_file, irods_server)

    return temp_directory


def _create_irods_server_container(docker_client: Client) -> Tuple[dict, int]:
    """
    Create iRODs test server.
    :param docker_client: the Docker client
    :return: a tuple where the first element is the created iRODS container and the second is the PORT that it is
    connected to the local machine on
    """
    open_port = get_open_port()

    host_config = docker_client.create_host_config(port_bindings={
        1247: open_port,
    })

    # Note: Unlike with Docker cli, docker-py does not appear to search for images on Docker Hub if they are not found
    # when building
    logging.info("Pulling iRODs server Docker image: %s - this may take a few minutes" % _IRODS_TEST_SERVER_DOCKER)
    response = [line for line in docker_client.pull(_IRODS_TEST_SERVER_DOCKER)]
    logging.debug(response)

    container_name = create_unique_container_name("irods")
    logging.info("Creating iRODs server Docker container: %s" % container_name)
    container = docker_client.create_container(
        image=_IRODS_TEST_SERVER_DOCKER, name=container_name, host_config=host_config, ports=[open_port])

    return container, open_port
