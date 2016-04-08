import logging
import os
import tempfile
from time import sleep

import atexit
from docker import Client

from testwithbaton._common import create_unique_container_name, create_client
from testwithbaton.models import ContainerisedIrodsServer, IrodsUser, IrodsServer

_IRODS_CONFIG_FILE_NAME = ".irodsEnv"

_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_ZONE_PARAMETER_NAME = "irodsZone"

_IRODS_TEST_SERVER_DOCKER = "mercury/icat:3.3.1"
_IRODS_TEST_SERVER_USERNAME = "rods"
_IRODS_TEST_SERVER_PASSWORD = "rods"
_IRODS_TEST_SERVER_ZONE = "iplant"


def start_irods() -> IrodsServer:
    """
    Starts iRODS server.
    :return: the started iRODS server
    """
    logging.info("Starting iRODS server in Docker container")

    docker_client = create_client()
    irods_server_container = None
    started = False

    def kill_container():
        try:
            if irods_server_container is not None:
                docker_client.kill(irods_server_container.native_object)
        except Exception:
            pass

    while not started:
        irods_server_container = _create_irods_server(docker_client)
        atexit.register(kill_container)
        docker_client.start(irods_server_container.native_object)

        started = _wait_for_start(docker_client, irods_server_container)
        if not started:
            logging.warning("iRODS server did not start correctly - restarting...")
            docker_client.kill(irods_server_container.native_object)

    assert irods_server_container is not None
    atexit.unregister(kill_container)
    # This is a gap here where unexpected termination will leave the container running
    return irods_server_container


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
    :param docker_client: the Docker client used to start the server
    :return: the location of the "volume" (i.e. directory) containing the configuration
    """
    temp_directory = tempfile.mkdtemp(prefix="irods-config-")
    logging.info("Created temp directory for iRODS config: %s" % temp_directory)
    os.chmod(temp_directory, 0o777)

    connection_file = os.path.join(temp_directory, _IRODS_CONFIG_FILE_NAME)
    write_irods_server_connection_settings(connection_file, irods_server)

    return temp_directory


def _create_irods_server(docker_client: Client) -> ContainerisedIrodsServer:
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
    container = docker_client.create_container(image=_IRODS_TEST_SERVER_DOCKER, name=container_name, ports=[1247])

    irods_server = ContainerisedIrodsServer()
    irods_server.native_object = container
    irods_server.name = container_name
    irods_server.users = [
        IrodsUser(_IRODS_TEST_SERVER_USERNAME, _IRODS_TEST_SERVER_ZONE, _IRODS_TEST_SERVER_PASSWORD, True)
    ]
    return irods_server


def _wait_for_start(docker_client: Client, irods_test_server: ContainerisedIrodsServer) -> bool:
    """
    Waits for the givne containerized iRODS server to start.
    FIXME: These start checks are likely to be coupled with iRODS 3.3.1
    :param docker_client: the Docker client
    :param irods_test_server: the containerised server
    """
    # Block until iRODS says that is has started
    logging.info("Waiting for iRODS server to have setup")
    for line in docker_client.logs(irods_test_server.native_object, stream=True):
        logging.debug(line)
        if "exited: irods" in str(line):
            if "not expected" in str(line):
                return False
            else:
                break

    # Just because iRODS says it has started, it appears that it does not mean it is ready to do queries
    status_query = docker_client.exec_create(irods_test_server.name,
                                       "su - irods -c \"/home/irods/iRODS/irodsctl --verbose status\"", stdout=True)
    while "No servers running" in docker_client.exec_start(status_query).decode("utf8"):
        # Nothing else to check on - just sleep it out
        logging.info("Still waiting on iRODS setup")
        sleep(0.5)

    return True
