import logging
from time import sleep

from testwithbaton.api import setup_test_with_baton


logging.root.setLevel("DEBUG")

test_with_baton = setup_test_with_baton()

print(test_with_baton.get_baton_binaries_location())

sleep(600)
test_with_baton.tear_down()