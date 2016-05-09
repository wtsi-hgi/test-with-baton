from threading import Thread, Semaphore, Lock, BoundedSemaphore
from typing import Dict, Callable, List

import atexit

from testwithbaton.models import ContainerisedIrodsServer


class IrodsServerHeater():
    """
    TODO
    """
    # TODO: Just take iRODS contorller as an argument
    def __init__(self, server_starter: Callable[[], ContainerisedIrodsServer],
                 server_stopper: Callable[[ContainerisedIrodsServer], None], max_hot_servers: int=10):
        """
        Constructor.
        :param server_starter: method that can start iRODS server
        :param server_stopper: method that can stops iRODS servers
        :param max_hot_servers: the maximum number of servers to keep hot
        """
        self._server_starter = server_starter
        self._server_stopper = server_stopper
        self._max_hot_servers = max_hot_servers
        self._hot_servers = []   # type: List[ContainerisedIrodsServer]
        self._consumer_semaphore = Semaphore(0)
        self._producer_semaphore = BoundedSemaphore(self.max_hot_servers)
        self._stopped = True
        self._state_change_lock = Lock()

    @property
    def max_hot_servers(self) -> int:
        """
        Gets the maximum number of servers that are kept hot.
        :return: the maximum number of hot servers
        """
        return self._max_hot_servers

    def start(self):
        """
        Starts the iRODS server heater.
        """
        with self._state_change_lock:
            if not self._stopped:
                raise RuntimeError("Already started")
            self._stopped = False
            atexit.register(self.stop)

            def endless_warmer():
                while not self._stopped:
                    self._warmer()

            for _ in range(self.max_hot_servers):
                Thread(target=endless_warmer).start()

    def stop(self):
        """
        Stops the iRODS server heater.
        """
        with self._state_change_lock:
            if not self._stopped:
                self._stopped = True

                while self.get_number_of_hot_servers() > 0:
                    server = self.take_hot_server()
                    self._server_stopper(server)

                atexit.unregister(self.stop)

    def get_number_of_hot_servers(self) -> int:
        """
        Gets the number of servers that are hot and ready for use.
        :return: number of hot servers
        """
        return len(self._hot_servers)

    def take_hot_server(self) -> ContainerisedIrodsServer:
        """
        TODO
        :return:
        """
        self._consumer_semaphore.acquire()
        server = self._hot_servers.pop(0)
        self._producer_semaphore.release()
        return server

    def _warmer(self):
        """
        TODO
        :param server:
        """
        self._producer_semaphore.acquire()
        server = self._server_starter()
        self._hot_servers.append(server)
        assert self.get_number_of_hot_servers() <= self.max_hot_servers
        self._consumer_semaphore.release()


_heated = dict()    # type: Dict[type, type]


def use_heater(irods_server_controller_type: type, max_hot_servers: int) -> type:
    """
    TODO
    :param irods_server_controller_type:
    :param max_hot_servers:
    :return:
    """
    # FIXME: Resolve issue in:
    # 1) Losing reference to heated
    # 2) Caching different numbers of hot servers

    if irods_server_controller_type not in _heated:
        controller = irods_server_controller_type()
        heater = IrodsServerHeater(controller.start_server, controller.stop_server, max_hot_servers)
        heater.start()

        _heated[irods_server_controller_type] = type(
            "Heated%s" % irods_server_controller_type.__name__,
            (irods_server_controller_type, ),
            {
                "_heater": heater,
                "start_server": lambda self: heater.take_hot_server()
            }
        )
    return _heated[irods_server_controller_type]
