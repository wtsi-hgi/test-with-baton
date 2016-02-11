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

    return Client(**kwargs_from_env(assert_hostname=False), version="auto")


def create_unique_container_name(name_hint: str="") -> str:
    """
    Creates a unique build_name for the container with an optional name hint.
    :param name_hint: optional name hint
    :return: unique build_name with the build_name hint if given
    """
    if name_hint is not "":
        name_hint = "%s-" % name_hint
    return "%s%s" % (name_hint, uuid4())
