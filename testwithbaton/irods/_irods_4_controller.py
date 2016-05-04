import atexit
import json
import logging
import os
from abc import ABCMeta
from time import sleep

from testwithbaton.irods._irods_contoller import IrodsServerController
from testwithbaton.models import IrodsServer, ContainerisedIrodsServer, IrodsUser, Version

_IRODS_CONFIG_FILE_NAME = "irods_environment.json"

_IRODS_HOST_PARAMETER_NAME = "irods_host"
_IRODS_PORT_PARAMETER_NAME = "irods_port"
_IRODS_USERNAME_PARAMETER_NAME = "irods_user_name"
_IRODS_ZONE_PARAMETER_NAME = "irods_zone_name"


class Irods4ServerController(IrodsServerController, metaclass=ABCMeta):
    """
    Controller for containerised iRODS 4 servers.
    """
    @staticmethod
    def write_connection_settings(file_location: str, irods_server: IrodsServer):
        if os.path.isfile(file_location):
            raise ValueError("Settings cannot be written to a file that already exists")

        user = irods_server.users[0]
        config = {
            _IRODS_USERNAME_PARAMETER_NAME: user.username,
            _IRODS_HOST_PARAMETER_NAME: irods_server.host,
            _IRODS_PORT_PARAMETER_NAME: irods_server.port,
            _IRODS_ZONE_PARAMETER_NAME: user.zone
        }
        config_as_json = json.dumps(config)
        logging.debug("Writing iRODS connection config to: %s" % file_location)
        with open(file_location, 'w') as settings_file:
            settings_file.write(config_as_json)


class Irods4_1_8ServerController(Irods4ServerController):
    """
    Controller for containerised iRODS 4.1.8 servers.
    """
    _IMAGE_NAME = "mercury/icat:4.1.8"
    _USERS = [
        IrodsUser("rods", "testZone", "irods123", admin=True)
    ]
    _VERSION = Version("4.1.8")

    def __init__(self):
        super().__init__(
            Irods4_1_8ServerController._IMAGE_NAME,
            Irods4_1_8ServerController._VERSION,
            Irods4_1_8ServerController._USERS
        )

    def _wait_for_start(self, container: ContainerisedIrodsServer) -> bool:
        logging.info("Waiting for iRODS server to have setup")
        for line in self.docker_client.logs(container.native_object, stream=True):
            logging.debug(line)
            if "iRODS server started successfully!" in str(line):
                return True
            elif "iRODS server failed to start." in str(line):
                return False
