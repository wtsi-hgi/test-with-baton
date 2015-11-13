import logging

from testwithbaton.baton_proxies import build_baton_docker, create_baton_proxy_binaries
from testwithbaton.common import create_client
from testwithbaton.irods_server import create_irods_test_server


def setup_test_with_baton():
    return TestWithBatonSetup()


class TestWithBatonSetup:
    """
    TODO
    """
    # TODO: Allow settings
    def __init__(self):
        """
        TODO
        """
        self._irods_test_server = None
        self._baton_binaries_location = None

    def setup(self):
        """
        TODO
        """
        if self._baton_binaries_location is not None:
            raise RuntimeError("Already setup")
        assert self._irods_test_server is None

        docker_client = create_client()

        build_baton_docker(docker_client)

        irods_test_server = create_irods_test_server(docker_client)
        docker_client.start(irods_test_server.container)
        build_baton_docker(docker_client)
        self._baton_binaries_location = create_baton_proxy_binaries(irods_test_server)

        logging.info("Starting iRODS server in Docker container on port: %d" % irods_test_server.port)
        docker_client.start(irods_test_server.container)

        self._irods_test_server = irods_test_server

    def get_baton_binaries_location(self):
        """
        TODO
        :return:
        """
        if self._baton_binaries_location is None:
            self.setup()
        return self._baton_binaries_location

    def tear_down(self):
        docker_client = create_client()
        docker_client.kill(self._irods_test_server.container)