import logging

from docker import Client
from docker.utils import kwargs_from_env

from testwithbaton.api import TestWithBatonSetup





logging.root.setLevel("DEBUG")

test_with_baton = TestWithBatonSetup()
test_with_baton.setup()

