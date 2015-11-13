import logging
from time import sleep

from testwithbaton.api import TestWithBatonSetup

logging.root.setLevel("DEBUG")

test_with_baton = TestWithBatonSetup()
test_with_baton.setup()

print(test_with_baton.get_baton_binaries_location())

sleep(600)
test_with_baton.tear_down()