import logging
import weakref
from typing import Optional
from uuid import uuid4

from docker import Client
from docker.tls import TLSConfig
from docker.utils import kwargs_from_env

_client = None


def _create_client(base_url: str, tls: TLSConfig=False) -> Optional[Client]:
    """
    Creates a Docker client with the given details.
    :param base_url: the base URL of the Docker daemon
    :param tls: the Docker daemon's TLS config (if any)
    :return: the created client else None if unable to connect the client to the daemon
    """
    try:
        client = Client(base_url=base_url, tls=tls, version="auto")
        return client if client.ping() == "OK" else None
    except:
        return None


def create_client() -> Client:
    """
    Clients a Docker client.

    Will raise a `ConnectionError` if the Docker daemon is not accessible
    :return: the Docker client
    """
    global _client
    if _client is None:
        # First try looking at the environment variables for specification of the daemon's location
        docker_environment = kwargs_from_env(assert_hostname=False)
        if "base_url" in docker_environment:
            client = _create_client(docker_environment.get("base_url"), docker_environment.get("tls"))
            if client is None:
                raise ConnectionError(
                    "Could not connect to the Docker daemon specified by the `DOCKER_X` environment variables: %s"
                    % docker_environment)
            else:
                logging.info("Connected to Docker daemon specified by the environment variables")
        else:
            # Let's see if the Docker daemon is accessible via the UNIX socket
            client = _create_client("unix://var/run/docker.sock")
            if client is not None:
                logging.info("Connected to Docker daemon running on UNIX socket")
            else:
                raise ConnectionError(
                    "Cannot connect to Docker - is the Docker daemon running? `$DOCKER_HOST` should be set or the "
                    "daemon should be accessible via the standard UNIX socket.")
        _client = weakref.ref(client)
    client = _client()
    assert isinstance(client, Client)
    return client


def create_unique_name(name_hint: str="") -> str:
    """
    Creates a unique name with an optional name hint.
    :param name_hint: optional name hint
    :return: unique name that includes the hint if given
    """
    if name_hint is not "":
        name_hint = "%s-" % name_hint
    return "%s%s" % (name_hint, uuid4())
