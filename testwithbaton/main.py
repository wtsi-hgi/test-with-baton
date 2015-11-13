import os
from time import sleep

import subprocess
from docker import Client
from docker.utils import kwargs_from_env

from testwithbaton.baton_proxies import create_baton_proxy_binaries, build_baton_docker
from testwithbaton.irods_test_server import create_irods_test_server


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



def shell_source(script):
    """Sometime you want to emulate the action of "source" in bash,
    settings some environment variables. Here is a way to do it."""
    import subprocess, os
    pipe = subprocess.Popen(". %s; env" % script, stdout=subprocess.PIPE, shell=True)
    output = pipe.communicate()[0]
    env = dict((line.split("{0}".format("=".encode("UTF-8")), 1) for line in output.splitlines()))
    print(env)
    os.environ.update(env)



shell_source("/Applications/Docker/Docker Quickstart Terminal.app/Contents/Resources/Scripts/start.sh")


docker_client = create_client()

irods_test_server = create_irods_test_server(docker_client)
docker_client.start(irods_test_server)

build_baton_docker(docker_client)
baton_binaries = create_baton_proxy_binaries(irods_test_server)

print(baton_binaries)






sleep(10)

# TODO: Ensure kill, regardless of exception
docker_client.kill(irods_test_server.container)



