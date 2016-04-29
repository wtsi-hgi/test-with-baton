import atexit
import logging
import os
from abc import ABCMeta
from time import sleep

from testwithbaton.irods._irods_contoller import IrodsServerController
from testwithbaton.models import IrodsServer, ContainerisedIrodsServer, IrodsUser

_IRODS_CONFIG_FILE_NAME = ".irodsEnv"

_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_ZONE_PARAMETER_NAME = "irodsZone"


class Irods3ServerController(IrodsServerController, metaclass=ABCMeta):
    """
    Controller for containerised iRODS 3 servers.
    """
    @staticmethod
    def write_connection_settings(file_location: str, irods_server: IrodsServer):
        if os.path.isfile(file_location):
            raise ValueError("Settings cannot be written to a file that already exists")

        user = irods_server.users[0]
        config = [
            (_IRODS_USERNAME_PARAMETER_NAME, user.username),
            (_IRODS_HOST_PARAMETER_NAME, irods_server.host),
            (_IRODS_PORT_PARAMETER_NAME, irods_server.port),
            (_IRODS_ZONE_PARAMETER_NAME, user.zone)
        ]
        logging.debug("Writing iRODS connection config to: %s" % file_location)
        with open(file_location, 'w') as settings_file:
            settings_file.write('\n'.join(["%s %s" % x for x in config]))


class Irods3_3_1ServerController(Irods3ServerController):
    """
    Controller for containerised iRODS 3.3.1 servers.
    """
    _IMAGE_NAME = "mercury/icat:3.3.1"
    _USERS = [
        IrodsUser("rods", "iplant", "rods", admin=True)
    ]

    def start_server(self) -> ContainerisedIrodsServer:
        logging.info("Starting iRODS server in Docker container")

        container = None
        started = False

        while not started:
            container = self._create_container(
                Irods3_3_1ServerController._IMAGE_NAME, Irods3_3_1ServerController._USERS)
            atexit.register(self.stop_server, container)
            self.docker_client.start(container.native_object)

            started = self._wait_for_start(container)
            if not started:
                logging.warning("iRODS server did not start correctly - restarting...")
                self.docker_client.kill(container.native_object)
        assert container is not None

        self._cache_started_container(container)

        return container

    def stop_server(self, container: ContainerisedIrodsServer):
        try:
            if container is not None:
                self.docker_client.kill(container.native_object)
        except Exception:
            # TODO: Should not use such a general exception
            pass

    def _wait_for_start(self, container: ContainerisedIrodsServer) -> bool:
        """
        Waits for the given containerized iRODS server to start.
        :param irods_test_server: the containerised server
        """
        # Block until iRODS says that is has started
        logging.info("Waiting for iRODS server to have setup")
        for line in self.docker_client.logs(container.native_object, stream=True):
            logging.debug(line)
            if "exited: irods" in str(line):
                if "not expected" in str(line):
                    return False
                else:
                    break

        # Just because iRODS says it has started, it does not mean it is ready to do queries!
        status_query = self.docker_client.exec_create(
            container.name, "su - irods -c \"/home/irods/iRODS/irodsctl --verbose status\"", stdout=True)
        while "No servers running" in self.docker_client.exec_start(status_query).decode("utf8"):
            # Nothing else to check on - just sleep it out
            logging.info("Still waiting on iRODS setup")
            sleep(0.5)

        return True

    def _cache_started_container(self, container: ContainerisedIrodsServer):
        """
        Caches the started container.
        :param container: the container to created cached image for
        """
        cached_image_name = IrodsServerController._cached_image_name(Irods3_3_1ServerController._IMAGE_NAME)
        if len(self.docker_client.images(cached_image_name, quiet=True)) == 0:
            # Cache started container
            repository, tag = cached_image_name.split(":")
            self.docker_client.commit(container.native_object["Id"], repository=repository, tag=tag)
