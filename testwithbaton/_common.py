import socket
from urllib.parse import urlparse
from uuid import uuid4

from docker import Client
from docker.utils import kwargs_from_env


def create_client() -> Client:
    """
    Clients a Docker client.

    Will raise a `ConnectionError` if the Docker daemon is not running.
    :return: the Docker client
    """
    docker_environment = kwargs_from_env(assert_hostname=False)

    if "base_url" not in docker_environment:
        raise ConnectionError(
            "Cannot connect to Docker - is the Docker daemon running? `$DOCKER_HOST` should be set.")

    return Client(**kwargs_from_env(assert_hostname=False))


def create_unique_container_name(name_hint: str="") -> str:
    """
    Creates a unique build_name for the container with an optional name hint.
    :param name_hint: optional name hint
    :return: unique build_name with the build_name hint if given
    """
    if name_hint is not "":
        name_hint = "%s-" % name_hint
    return "%s%s" % (name_hint, uuid4())


def find_hostname(docker_client: Client) -> str:
    """
    Finds the hostname of the given Docker client.
    :param docker_client: the client to find the hostname of
    :return: the hostname of the client
    """
    docker_url = kwargs_from_env(assert_hostname=False)["base_url"]
    parsed_docker_url = urlparse(docker_url)
    hostname = parsed_docker_url.hostname
    assert hostname is not None
    return hostname


def get_open_port() -> int:
    """
    Gets a PORT that will (probably) be available on the machine.

    It is possible that in-between the time in which the open PORT of found and when it is used, another process may
    bind to it instead.
    :return: the (probably) available PORT
    """
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(("", 0))
    free_socket.listen(1)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port
