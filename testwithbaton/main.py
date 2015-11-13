import logging
from time import sleep

from docker import Client
from docker.utils import kwargs_from_env

from testwithbaton.baton_proxies import create_baton_proxy_binaries, build_baton_docker
from testwithbaton.irods_server import create_irods_test_server


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




logging.root.setLevel("DEBUG")

docker_client = create_client()


build_baton_docker(docker_client)


irods_test_server = create_irods_test_server(docker_client)
docker_client.start(irods_test_server.container)
build_baton_docker(docker_client)
baton_binaries = create_baton_proxy_binaries(irods_test_server)

print(baton_binaries)


docker_client.start(irods_test_server.container)





sleep(100)

# TODO: Ensure kill, regardless of exception
docker_client.kill(irods_test_server.container)



