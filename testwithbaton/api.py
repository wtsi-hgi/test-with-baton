import atexit
import logging
import shutil

import sys
from docker import Client

from testwithbaton.common import create_client
from testwithbaton.irods_server import create_irods_test_server
from testwithbaton.models import IrodsServer
from testwithbaton.proxies import build_baton_docker, create_baton_proxy_binaries, create_icommands_proxy_binaries


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

        self._irods_test_server = create_irods_test_server(docker_client)
        self._start_irods(docker_client, self._irods_test_server)

        build_baton_docker(docker_client)
        self.baton_location = create_baton_proxy_binaries(self._irods_test_server)
        self.icommands_location = create_icommands_proxy_binaries(self._irods_test_server)

    def tear_down(self):
        """
        TODO
        """
        if self._irods_test_server is not None:
            logging.debug("Killing client")
            docker_client = create_client()
            try:
                docker_client.kill(self._irods_test_server.container)
            except Exception as error:
                logging.error(error)
            self._irods_test_server = None

            logging.debug("Removing temp folders")
            try:
                shutil.rmtree(self.baton_location)
            except Exception as error:
                logging.error(error)
            self.baton_location = None
            try:
                shutil.rmtree(self.icommands_location)
            except Exception as error:
                logging.error(error)
            self.icommands_location = None

        atexit.unregister(self.tear_down)
        logging.debug("Tear down complete")

    @staticmethod
    def _start_irods(docker_client: Client, irods_test_server: IrodsServer):
        """
        TODO
        :param docker_client:
        :param irods_test_server:
        :return:
        """
        logging.info("Starting iRODS server in Docker container on port: %d" % irods_test_server.port)
        docker_client.start(irods_test_server.container)

        # Block until iRODS is setup
        logging.info("Waiting for iRODS server to have setup")
        for line in docker_client.logs(irods_test_server.container, stream=True):
            logging.debug(line)
            if "exited: irods" in str(line):
                break
