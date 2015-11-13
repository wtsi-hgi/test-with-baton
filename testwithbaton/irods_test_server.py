from typing import Tuple

from docker import Client

from testwithbaton import models
from testwithbaton.common import create_unique_container_name, get_open_port, find_hostname
from testwithbaton.models import IrodsUser, IrodsServer

_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_ZONE_PARAMETER_NAME = "irodsZone"

_IRODS_SERVER_DOCKER = "agaveapi/irods:3.3.1"
_IRODS_USERNAME = "testuser"
_IRODS_PASSWORD = "testuser"
_IRODS_ZONE = "iplant"


def create_irods_test_server(docker_client: Client) -> models:
    """
    TODO
    :param docker_client:
    :return:
    """
    container, port = _create_irods_server_container(docker_client)
    hostname = find_hostname(docker_client)
    users = [IrodsUser(_IRODS_USERNAME, _IRODS_PASSWORD, _IRODS_ZONE)]

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
    settings_file = open(write_to, 'w')
    settings_file.write(["%s %s\n" % x for x in config])
    settings_file.close()


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

    container = docker_client.create_container(
        image=_IRODS_SERVER_DOCKER, name=create_unique_container_name("irods"), host_config=host_config)

    return container, open_port
