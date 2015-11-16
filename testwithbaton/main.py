import logging
from time import sleep

import atexit

from testwithbaton.api import create_test_with_baton


logging.root.setLevel("DEBUG")

test_with_baton = create_test_with_baton()

print(test_with_baton.get_baton_binaries_location())


atexit.register(test_with_baton.tear_down)

sleep(600)
test_with_baton.tear_down()

