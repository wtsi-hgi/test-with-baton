import logging
import os
import tempfile
from logging import Logger
from time import sleep
from typing import Tuple

from docker import Client

from testwithbaton import models
from testwithbaton.common import create_unique_container_name, get_open_port, find_hostname
from testwithbaton.models import IrodsUser, IrodsServer

_IRODS_CONFIG_FILE_NAME = ".irodsEnv"

# TODO: Should be settings?
_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_ZONE_PARAMETER_NAME = "irodsZone"

_IRODS_TEST_SERVER_DOCKER = "agaveapi/irods:3.3.1"
_IRODS_TEST_SERVER_USERNAME = "testuser"
_IRODS_TEST_SERVER_PASSWORD = "testuser"
_IRODS_TEST_SERVER_ZONE = "iplant"


def create_irods_test_server(docker_client: Client) -> models:
    """
    TODO
    :param docker_client:
    :return:
    """
    container, port = _create_irods_server_container(docker_client)
    hostname = find_hostname(docker_client)
    users = [IrodsUser(_IRODS_TEST_SERVER_USERNAME, _IRODS_TEST_SERVER_PASSWORD, _IRODS_TEST_SERVER_ZONE)]

    return IrodsServer(container, hostname, port, users)


def write_irods_server_connection_settings(write_to: str, irods_server: IrodsServer):
    """
    TODO
    :param write_to:
    :param irods_server:
    :return:
    """
    user = irods_server.users[0]
    config = [
        (_IRODS_USERNAME_PARAMETER_NAME, user.username),
        (_IRODS_HOST_PARAMETER_NAME, irods_server.host),
        (_IRODS_PORT_PARAMETER_NAME, irods_server.port),
        (_IRODS_ZONE_PARAMETER_NAME, user.zone)
    ]
    logging.debug("Writing iRODS connection config to: %s" % write_to)
    settings_file = open(write_to, 'w')
    settings_file.write('\n'.join(["%s %s" % x for x in config]))
    settings_file.close()


def create_irods_config_volume(irods_server: IrodsServer) -> str:
    """
    TODO
    :param irods_server:
    :return: the location of "volume" (i.e. directory) containing the configuration
    """
    temp_directory = tempfile.mkdtemp(prefix="irods-config-")
    logging.info("Created temp directory for iRODS config: %s" % temp_directory)

    connection_file = os.path.join(temp_directory, _IRODS_CONFIG_FILE_NAME)
    write_irods_server_connection_settings(connection_file, irods_server)

    return temp_directory


def _create_irods_server_container(docker_client: Client) -> Tuple[dict, int]:
    """
    Create iRODs test server.
    :param docker_client: the Docker client
    :return:
    """
    open_port = get_open_port()

    host_config = docker_client.create_host_config(port_bindings={
        open_port: 1247,
    })

    # Note: Unlike with Docker cli, docker-py does not appear to search for images on Docker Hub if they are not found
    # when building
    logging.info("Pulling iRODs server Docker image: %s - this may take a few minutes" % _IRODS_TEST_SERVER_DOCKER)
    print(docker_client.pull(_IRODS_TEST_SERVER_DOCKER))

    logging.debug("Creating iRODs server Docker container")
    container = docker_client.create_container(
        image=_IRODS_TEST_SERVER_DOCKER, name=create_unique_container_name("irods"), host_config=host_config)

    return container, open_port
