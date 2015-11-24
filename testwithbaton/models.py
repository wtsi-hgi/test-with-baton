from typing import List

from irodscommon.models import IrodsServer
from irodscommon.models import IrodsUser


class ContainerisedIrodsServer(IrodsServer):
    """
    Model of an iRODS server that runs in a container.
    """
    def __init__(self, container: dict, host: str, port: int, users: List[IrodsUser]):
        super(ContainerisedIrodsServer, self).__init__(host, port, users)
        self.container = container
