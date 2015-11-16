import logging

import atexit

import shutil

from testwithbaton.proxies import build_baton_docker, create_baton_proxy_binaries, create_icommands_proxy_binaries
from testwithbaton.common import create_client
from testwithbaton.irods_server import create_irods_test_server


class TestWithBatonSetup:
    """
    TODO
    """
    # TODO: Allow settings
    def __init__(self):
        """
        Default constructor.
        """
        self._irods_test_server = None
        self.baton_location = None
        self.icommands_location = None

    def setup(self):
        """
        TODO
        """
        if self.baton_location is not None:
            raise RuntimeError("Already setup")
        assert self._irods_test_server is None

        # Ensure that no matter what happens, tear down is done
        atexit.register(self.tear_down)

        docker_client = create_client()
        build_baton_docker(docker_client)

        irods_test_server = create_irods_test_server(docker_client)
        docker_client.start(irods_test_server.container)
        build_baton_docker(docker_client)

        logging.info("Starting iRODS server in Docker container on port: %d" % irods_test_server.port)
        docker_client.start(irods_test_server.container)

        self._irods_test_server = irods_test_server

        self.baton_location = create_baton_proxy_binaries(irods_test_server)
        self.icommands_location = create_icommands_proxy_binaries(irods_test_server)


    def tear_down(self):
        """
        TODO
        """
        if self._irods_test_server is not None:
            logging.debug("Killing client")
            docker_client = create_client()
            docker_client.kill(self._irods_test_server.container)

            logging.debug("Removing temp folders")
            shutil.rmtree(self.baton_location)
            shutil.rmtree(self.icommands_location)

        atexit.unregister(self.tear_down)

        logging.debug("Tearing down complete")
        # TODO: Clean-up temp folders


def create_test_with_baton() -> TestWithBatonSetup:
    """
    TODO
    :return:
    """
    test_with_baton = TestWithBatonSetup()
    test_with_baton.setup()
    return test_with_baton