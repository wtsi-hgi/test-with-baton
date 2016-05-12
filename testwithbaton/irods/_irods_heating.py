from typing import Dict, Set

from threading import Lock, Semaphore, Thread
from typing import List

from testwithbaton.irods import StaticIrodsServerController
from testwithbaton.models import ContainerisedIrodsServer


def take_hot_server(controller_cls: type):
    pass




class HeatedStaticIrodsServerController(StaticIrodsServerController):
    """
    TODO
    """
    MAX_HOT_SERVERS = 10
    _HOT_SERVERS = []    # type: List[ContainerisedIrodsServer]
    _SERVERS_SEMAPHORE = Semaphore()

    @staticmethod
    def get_number_of_hot_servers() -> int:
        """
        Gets the number of servers that are hot and ready for use.
        :return: number of hot servers
        """
        return len(HeatedStaticIrodsServerController._HOT_SERVERS)

    @staticmethod
    def start_server() -> ContainerisedIrodsServer:
        """
        TODO
        :return:
        """
        with HeatedStaticIrodsServerController._SERVERS_SEMAPHORE:
            HeatedStaticIrodsServerController._HOT_SERVERS.pop(0)
            Thread()

    @staticmethod
    def _add_hot_server():
        irods_server = super().start_server()
        HeatedStaticIrodsServerController._HOT_SERVERS.append(irods_server)
        HeatedStaticIrodsServerController._SERVERS_SEMAPHORE.release()

