from enum import Enum, unique

from testwithbaton.irods._irods_3_controller import StaticIrods3_3_1ServerController
from testwithbaton.irods._irods_4_controller import StaticIrods4_1_8ServerController
from testwithbaton.irods._irods_contoller import StaticIrodsServerController


@unique
class IrodsVersion(Enum):
    """
    Enum mapping between iRODS server versions and the related server controllers.
    """
    v3_3_1 = StaticIrods3_3_1ServerController
    v4_1_8 = StaticIrods4_1_8ServerController


def get_static_irods_server_controller(irods_version: IrodsVersion=IrodsVersion.v3_3_1) -> StaticIrodsServerController:
    """
    Gets a controller for the an iRODS server of the given version.
    :param irods_version: the iRODS version that the controller must work with
    :return: the iRODS server controller
    """
    return irods_version.value
