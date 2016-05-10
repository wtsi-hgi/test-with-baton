import unittest

from testwithbaton.irods._api import get_irods_server_controller, IrodsVersion
from testwithbaton.irods._irods_3_controller import Irods3_3_1ServerController
from testwithbaton.irods._irods_4_controller import Irods4_1_8ServerController


class TestGetIrodsServerController(unittest.TestCase):
    """
    Tests for `get_irods_server_controller`.
    """
    def test_get_v_3_3_1(self):
        irods_controller = get_irods_server_controller(IrodsVersion.v3_3_1)
        self.assertIsInstance(irods_controller, Irods3_3_1ServerController)

    def test_get_v_4_1_8(self):
        irods_controller = get_irods_server_controller(IrodsVersion.v4_1_8)
        self.assertIsInstance(irods_controller, Irods4_1_8ServerController)


if __name__ == "__main__":
    unittest.main()
