import unittest
from abc import ABCMeta, abstractmethod

from testwithbaton._common import create_client
from testwithbaton._proxies import ICommandProxyController
from testwithbaton.helpers import SetupHelper
from testwithbaton.irods._irods_3_controller import Irods3_3_1ServerController
from testwithbaton.irods._irods_4_controller import Irods4_1_8ServerController
from testwithbaton.irods._irods_contoller import IrodsServerController
from testwithbaton.models import ContainerisedIrodsServer, Version


class TestIrodsServerController(unittest.TestCase, metaclass=ABCMeta):
    """
    Tests for `IrodsServerController`.
    """
    @staticmethod
    def _is_container_running(container: ContainerisedIrodsServer) -> bool:
        """
        Gets whether the given container is running. Will raise an exception if the container does not exist.
        :param container: the container
        :return: whether the container is running
        """
        docker_client = create_client()
        return docker_client.inspect_container(container.native_object)["State"]["Running"]

    @abstractmethod
    def create_controller(self) -> IrodsServerController:
        """
        Creates a concrete `IrodsServerController` instance.
        :return: an iRODS server controller
        """

    def __init__(self, compatible_baton_image: str, irods_version: Version, *args, **kwargs):
        """
        Constructor.
        :param compatible_baton_image: version of baton compatible with the version of iRODS that is controlled
        :param irods_version: the iRODS version that the server controller deals with
        :param args: used by `unittest.TestCase`
        :param kwargs: used by `unittest.TestCase`
        """
        super().__init__(*args, **kwargs)
        self.compatible_baton_image = compatible_baton_image
        self.irods_version = irods_version

    def setUp(self):
        self.irods_controller = self.create_controller()

    def test_start_server(self):
        irods_server = self.irods_controller.start_server()
        self.assertTrue(self._is_container_running(irods_server))

        repository, tag = self.compatible_baton_image.split(":")
        create_client().pull(repository, tag)

        proxy_controller = ICommandProxyController(irods_server, self.compatible_baton_image)
        icommand_binaries_location = proxy_controller.create_proxy_binaries()
        setup_helper = SetupHelper(icommand_binaries_location)

        self.assertEqual(setup_helper.get_icat_version(), self.irods_version)

    def test_stop_server(self):
        irods_container = self.irods_controller.start_server()
        assert self._is_container_running(irods_container)
        self.irods_controller.stop_server(irods_container)
        self.assertFalse(self._is_container_running(irods_container))


class TestIrods3ServerController(TestIrodsServerController, metaclass=ABCMeta):
    """
    Tests for `_Irods3ServerController`.
    """
    _BATON_IMAGE = "mercury/baton:0.16.3-with-irods-3.3.1"

    def __init__(self, irods_version: Version, *args, **kwargs):
        super().__init__(self._BATON_IMAGE, irods_version, *args, **kwargs)


class TestIrods3_3_1ServerController(TestIrods3ServerController):
    """
    Tests for `Irods3_3_1ServerController`.
    """
    _IRODS_VERSION = "3.3.1"

    def __init__(self, *args, **kwargs):
        super().__init__(Version(self._IRODS_VERSION), *args, **kwargs)

    def create_controller(self) -> IrodsServerController:
        return Irods3_3_1ServerController()


class TestIrods4ServerController(TestIrodsServerController, metaclass=ABCMeta):
    """
    Tests for `_Irods4ServerController`.
    """
    _BATON_IMAGE = "mercury/baton:0.16.3-with-irods-4.1.8"

    def __init__(self, irods_version: Version, *args, **kwargs):
        super().__init__(self._BATON_IMAGE, irods_version, *args, **kwargs)


class TestIrods4_1_8ServerController(TestIrods4ServerController):
    """
    Tests for `Irods4_1_8ServerController`.
    """
    _IRODS_VERSION = "4.1.8"

    def __init__(self, *args, **kwargs):
        super().__init__(Version(self._IRODS_VERSION), *args, **kwargs)

    def create_controller(self) -> IrodsServerController:
        return Irods4_1_8ServerController()


# Required to stop unittest from running the
del TestIrodsServerController
del TestIrods3ServerController
del TestIrods4ServerController


if __name__ == "__main__":
    unittest.main()
