import json
import logging

from testwithbaton.api import create_test_with_baton


_EXIT_INPUTS = ["q", "quit", "exit", "stop"]


def main():
    # logging.root.setLevel("DEBUG")

    test_with_baton = create_test_with_baton()

    setup_information = {"baton": test_with_baton.get_baton_binaries_location()}
    logging.info("Printing")
    print(json.dumps(setup_information))

    # `input()` is blocking therefore this is not a spin loop
    _print_tear_down_help()
    while input() not in _EXIT_INPUTS:
        _print_tear_down_help()
        pass


def _print_tear_down_help():
    """
    Print help information on how to tear down.
    """
    print("To tear down, enter one of the following: %s" % [x for x in _EXIT_INPUTS])


if __name__ == '__main__':
    main()

