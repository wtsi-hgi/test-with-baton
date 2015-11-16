import json
import logging
import signal

import sys

from testwithbaton.api import TestWithBatonSetup


def main():
    """
    Main method.
    """
    test_with_baton = TestWithBatonSetup()
    test_with_baton.setup()

    setup_information = {
        "baton": test_with_baton.baton_location,
        "icommands": test_with_baton.icommands_location
    }

    logging.info("Dumping setup information")
    print(json.dumps(setup_information))
    sys.stdout.flush()

    def call_tear_down(*args, **kargs):
        test_with_baton.tear_down()

    signal.signal(signal.SIGHUP, call_tear_down)
    signal.pause()


if __name__ == '__main__':
    main()
