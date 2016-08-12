import json
import logging
import os
from abc import ABCMeta

from testwithbaton.irods._irods_contoller import IrodsServerController, create_static_irods_server_controller
from testwithbaton.models import IrodsServer, ContainerisedIrodsServer, IrodsUser, Version

_IRODS_CONFIG_FILE_NAME = "irods_environment.json"

_IRODS_HOST_PARAMETER_NAME = "irods_host"
_IRODS_PORT_PARAMETER_NAME = "irods_port"
_IRODS_USERNAME_PARAMETER_NAME = "irods_user_name"
_IRODS_ZONE_PARAMETER_NAME = "irods_zone_name"


class _Irods4ServerController(IrodsServerController, metaclass=ABCMeta):
    """
    Controller for containerised iRODS 4 servers.
    """
    def write_connection_settings(self, file_location: str, irods_server: IrodsServer):
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

    def _wait_for_start(self, container: ContainerisedIrodsServer) -> bool:
        logging.info("Waiting for iRODS server to have setup")
        for line in IrodsServerController._DOCKER_CLIENT.logs(container.native_object, stream=True):
            logging.debug(line)
            if "iRODS server started successfully!" in str(line):
                return True
            elif "iRODS server failed to start." in str(line):
                return False


class Irods4_1_8ServerController(_Irods4ServerController):
    """
    Controller for containerised iRODS 4.1.8 servers.
    """
    IMAGE_NAME = "mercury/icat:4.1.8"
    USERS = [
        IrodsUser("rods", "testZone", "irods123", admin=True)
    ]
    VERSION = Version("4.1.8")

    def start_server(self) -> ContainerisedIrodsServer:
        return self._start_server(Irods4_1_8ServerController.IMAGE_NAME, Irods4_1_8ServerController.VERSION,
                                  Irods4_1_8ServerController.USERS)


class Irods4_1_9ServerController(_Irods4ServerController):
    """
    Controller for containerised iRODS 4.1.9 servers.
    """
    IMAGE_NAME = "mercury/icat:4.1.9"
    USERS = [
        IrodsUser("rods", "testZone", "irods123", admin=True)
    ]
    VERSION = Version("4.1.9")

    def start_server(self) -> ContainerisedIrodsServer:
        return self._start_server(Irods4_1_9ServerController.IMAGE_NAME, Irods4_1_9ServerController.VERSION,
                                  Irods4_1_9ServerController.USERS)


# Static iRODS server controllers, implemented (essentially) using singletons
StaticIrods4_1_8ServerController = create_static_irods_server_controller(Irods4_1_8ServerController())
StaticIrods4_1_9ServerController = create_static_irods_server_controller(Irods4_1_9ServerController())
