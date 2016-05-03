from enum import Enum, unique
from typing import Dict

from testwithbaton.irods import IrodsServerController
from testwithbaton.irods._irods_3_controller import Irods3_3_1ServerController
from testwithbaton.irods._irods_4_controller import Irods4_1_8ServerController

_cached_irods_server_controllers = dict()   # type: Dict[IrodsVersion, IrodsServerController]


@unique
class IrodsVersion(Enum):
    """
    Enum mapping between iRODS server versions and the related server controllers.
    """
    v3_3_1 = Irods3_3_1ServerController
    v4_1_8 = Irods4_1_8ServerController


def get_irods_server_controller(irods_version: IrodsVersion=IrodsVersion.v3_3_1) -> IrodsServerController:
    """
    Gets a controller for the an iRODS server of the given version.
    :param irods_version: the iRODS version that the controller must work with
    :return: the iRODS server controller
    """
    if irods_version not in _cached_irods_server_controllers:
        _cached_irods_server_controllers[irods_version] = irods_version.value()
    assert _cached_irods_server_controllers[irods_version] is not None
    return _cached_irods_server_controllers[irods_version]
