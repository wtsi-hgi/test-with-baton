import logging
from time import sleep

from testwithbaton.baton_proxies import build_baton_docker, create_baton_proxy_binaries
from testwithbaton.common import create_client
from testwithbaton.irods_server import create_irods_test_server


class TestWithBatonSetup:
    """
    TODO
    """
    # TODO: Allow settings
    def __init__(self):
        """
        TODO
        """
        self._baton_binaries_location = None

    def setup(self):
        """
        TODO
        """
        if self._baton_binaries_location is not None:
            raise RuntimeError("Already setup")

        docker_client = create_client()

        build_baton_docker(docker_client)

        irods_test_server = create_irods_test_server(docker_client)
        docker_client.start(irods_test_server.container)
        build_baton_docker(docker_client)
        baton_binaries = create_baton_proxy_binaries(irods_test_server)

        logging.info("Starting iRODS server in Docker container on port: %d" % irods_test_server.port)
        docker_client.start(irods_test_server.container)

        print(baton_binaries)
        sleep(600)

        # TODO: Ensure kill, regardless of exception
        docker_client.kill(irods_test_server.container)
