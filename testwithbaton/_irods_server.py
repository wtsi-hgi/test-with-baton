import logging
import os
import tempfile

from docker import Client

from testwithbaton._common import create_unique_container_name
from testwithbaton.models import ContainerisedIrodsServer, IrodsUser, IrodsServer

_IRODS_CONFIG_FILE_NAME = ".irodsEnv"

_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_ZONE_PARAMETER_NAME = "irodsZone"

_IRODS_TEST_SERVER_DOCKER = "agaveapi/irods:3.3.1"
_IRODS_TEST_SERVER_USERNAME = "rods"
_IRODS_TEST_SERVER_PASSWORD = "rods"
_IRODS_TEST_SERVER_ZONE = "iplant"


def create_irods_test_server(docker_client: Client) -> ContainerisedIrodsServer:
    """
    Creates an iRODS test server in a Docker container.
    :param docker_client: a Docker client
    :return: model of the created iRODS server
    """
    # Note: Unlike with Docker cli, docker-py does not appear to search for images on Docker Hub if they are not found
    # when building
    logging.info("Pulling iRODs server Docker image: %s - this may take a few minutes" % _IRODS_TEST_SERVER_DOCKER)
    response = docker_client.pull(_IRODS_TEST_SERVER_DOCKER)
    logging.debug(response)

    container_name = create_unique_container_name("irods")
    logging.info("Creating iRODs server Docker container: %s" % container_name)
    container = docker_client.create_container(image=_IRODS_TEST_SERVER_DOCKER, name=container_name)

    irods_server = ContainerisedIrodsServer()
    irods_server.native_object = container
    irods_server.name = container_name
    irods_server.users = [
        IrodsUser(_IRODS_TEST_SERVER_USERNAME, _IRODS_TEST_SERVER_PASSWORD, _IRODS_TEST_SERVER_ZONE, True)
    ]
    return irods_server


def start_irods(docker_client: Client, irods_test_server: ContainerisedIrodsServer):
    """
    Starts iRODS server.
    :param docker_client: the Docker client used to start the server
    :param irods_test_server: the server setup
    """
    logging.info("Starting iRODS server in Docker container")
    docker_client.start(irods_test_server.native_object)

    # Block until iRODS is setup
    logging.info("Waiting for iRODS server to have setup")
    for line in docker_client.logs(irods_test_server.native_object, stream=True):
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
