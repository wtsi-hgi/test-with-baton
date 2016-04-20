import time
import unittest
from statistics import median
from typing import List

from testwithbaton.api import TestWithBatonSetup


class TestTimer(unittest.TestCase):
    """
    Unit tests for `TestWithBatonSetup`.
    """
    _NUMBER_OF_SETUPS = 100

    def setUp(self):
        self._setups = []    # type: List[TestWithBatonSetup]

    def tearDown(self):
        for setup in self._setups:
            setup.tear_down()

    def test_setup_time(self):
        times = []  # type: List[int]

        for i in range(TestTimer._NUMBER_OF_SETUPS):
            start_time = time.monotonic()
            test_with_baton_setup = self._create_test_with_baton_setup()
            test_with_baton_setup.setup()
            total_time = time.monotonic() - start_time
            times.append(total_time)
            test_with_baton_setup.tear_down()
            print("%d/%d" % (i + 1, TestTimer._NUMBER_OF_SETUPS))

        print("Startup times")
        print("Raw: %s" % times)
        print("Median: %f" % median(times))

    def _create_test_with_baton_setup(self) -> TestWithBatonSetup:
        """
        Creates a test with baton setup that is registered to ensure tear down at end of test.
        :return: the test with baton setup
        """
        test_with_baton_setup = TestWithBatonSetup()
        self._setups.append(test_with_baton_setup)
        return test_with_baton_setup