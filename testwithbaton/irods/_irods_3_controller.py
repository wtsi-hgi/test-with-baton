import atexit
import logging
import os
from abc import ABCMeta
from time import sleep

from testwithbaton.irods._irods_contoller import IrodsServerController
from testwithbaton.models import IrodsServer, ContainerisedIrodsServer, IrodsUser

_IRODS_CONFIG_FILE_NAME = ".irodsEnv"

_IRODS_HOST_PARAMETER_NAME = "irodsHost"
_IRODS_PORT_PARAMETER_NAME = "irodsPort"
_IRODS_USERNAME_PARAMETER_NAME = "irodsUserName"
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

    def __init__(self):
        super().__init__(Irods3_3_1ServerController._IMAGE_NAME, Irods3_3_1ServerController._USERS)

    def _wait_for_start(self, container: ContainerisedIrodsServer) -> bool:
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
