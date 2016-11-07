import argparse
import json
import logging
import signal
import sys

from testwithbaton.api import TestWithBaton, BatonSetup

_PROGRAM_DESCRIPTION = "Sets up version of baton connected to an iRODS server for use in testing"
_PROGRAM_BATON_VERSION_PARAMETER_NAME = "baton"
_PROGRAM_BATON_VERSION_PARAMETER_HELP = "Version of baton to setup: [0.16.1, 0.16.2, 0.16.3, 0.16.4, 0.17.0]"
_PROGRAM_IRODS_VERSION_PARAMETER_NAME = "irods"
_PROGRAM_IRODS_VERSION_PARAMETER_HELP = "Version of iRODS to setup: [3.3.1, 4.1.8, 4.1.9, 4.1.10]"

_DEFAULT_BATON_VERSION = "0.17.0"
_DEFAULT_IRODS_VERSION = "4.1.10"


def _parse_arguments() -> (str, str):
    """
    Parse the input arguments.
    :return: tuple where the first item is the baton version and the second item is the iRODS version, both in the form
    X.X.X
    """
    parser = argparse.ArgumentParser(description=_PROGRAM_DESCRIPTION)
    parser.add_argument("--%s" % _PROGRAM_BATON_VERSION_PARAMETER_NAME, dest="baton_version",
                        default=_DEFAULT_BATON_VERSION, help=_PROGRAM_BATON_VERSION_PARAMETER_HELP)
    parser.add_argument("--%s" % _PROGRAM_IRODS_VERSION_PARAMETER_NAME, dest="irods_version",
                        default=_DEFAULT_IRODS_VERSION, help=_PROGRAM_IRODS_VERSION_PARAMETER_HELP)

    args = parser.parse_args()
    return args.baton_version, args.irods_version


def _get_baton_setup(baton_version: str, irods_version: str) -> BatonSetup:
    """
    Gets the baton setup for the given baton and iRODS versions.
    :param baton_version: the baton version
    :param irods_version: the iRODS version
    :return: the baton setup
    """
    baton_setup_as_string = "v%s_WITH_IRODS_%s" % (baton_version.replace(".", "_"), irods_version.replace(".", "_"))
    if baton_setup_as_string not in BatonSetup.__dict__:
        raise ValueError("No setup for baton version %s and iRODS version %s" % (baton_version, irods_version))
    return BatonSetup.__dict__[baton_setup_as_string]


def main():
    """
    Main method.
    """
    baton_version, irods_version = _parse_arguments()
    baton_setup = _get_baton_setup(baton_version, irods_version)

    test_with_baton = TestWithBaton(baton_setup=baton_setup)
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


if __name__ == "__main__":
    main()
