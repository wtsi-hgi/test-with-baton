import logging
import os
import tempfile
from typing import List

from testwithbaton.models import IrodsServer, ContainerisedIrodsServer

_SHEBANG = "#!/usr/bin/env bash"

_BATON_BINARIES = ["baton", "baton-metaquery", "baton-get", "baton-chmod", "baton-list", "baton-metamod",
                   "baton-specificquery"]
_ICOMMAND_BINARIES = ["ibun", "icd", "ichksum", "ichmod", "icp", "idbug", "ienv", "ierror", "iexecmd", "iexit", "ifsck",
                      "iget", "igetwild", "ihelp", "iinit", "ilocate", "ils", "ilsresc", "imcoll", "imiscsvrinfo",
                      "imkdir", "imv", "ipasswd", "iphybun", "iphymv", "ips", "iput", "ipwd", "iqdel", "iqmod",
                      "iqstat", "iquest", "iquota", "ireg", "irepl", "irm", "irmtrash", "irsync", "irule", "iscan",
                      "isysmeta", "itrim", "iuserinfo", "ixmsg", "izonereport", "imeta", "iadmin"]


def create_baton_proxy_binaries(irods_test_server: IrodsServer, docker_build: str) -> str:
    """
    Creates binaries that act as proxies to the baton binaries in the baton Docker. Allows realistic baton installation,
    where binaries are called from a directory.
    :param irods_test_server: the iRODS server to create proxies to
    :param docker_build: the build name of the Docker image to run
    :return: the directory containing the baton proxy binaries
    """
    return _create_proxy_binaries(irods_test_server, docker_build, "baton-proxies-", _BATON_BINARIES)


def create_icommands_proxy_binaries(irods_test_server: IrodsServer, docker_build: str) -> str:
    """
    Creates binaries that act as proxies to the icommands in the baton Docker.
    :param irods_test_server: the iRODS server to create proxies to
    :param docker_build: the build name of the Docker image to run
    :return: the directory containing the icommand proxy binaries
    """
    return _create_proxy_binaries(irods_test_server, docker_build, "icommands-proxies-", _ICOMMAND_BINARIES)


def _create_proxy_binaries(
        irods_test_server: IrodsServer, docker_build: str, directory_prefix: str, binaries: List[str]) -> str:
    """
    Create proxies to the given binaries.
    :param irods_test_server: the iRODS server to create proxies to
    :param docker_build: the build name of the Docker image to run
    :param directory_prefix: the prefix of the directory to put the proxy binaries in
    :param binaries: the binaries to create proxies for
    :return: the location of the directory containing the proxy binaries
    """
    temp_directory = tempfile.mkdtemp(prefix=directory_prefix)
    logging.debug("Created temp directory for proxy binaries: %s" % temp_directory)

    # Create proxies
    for binary in binaries:
        file_path = os.path.join(temp_directory, binary)
        with open(file_path, 'w') as file:
            file.write("%s\n" % _SHEBANG)

            # FIXME: Hack to get iput to work
            if binary == "iput":
                # FIXME: allow other flags, handle no $1 given
                file.write("""
                        cd $(dirname "$1")
                        mountDirectory=$PWD
                        fileName=$(basename "$1")
                        %s
                """ % (
                    _create_docker_run_command(irods_test_server, docker_build, binary,
                                               other="-v \"$mountDirectory\":/tmp/input:ro",
                                               entry="\"/tmp/input/$fileName\"")
                ))
            else:
                file.write("%s\n" % _create_docker_run_command(irods_test_server, docker_build, binary))
        os.chmod(file_path, 0o770)

    return temp_directory


def _create_docker_run_command(
        irods_test_server: IrodsServer, docker_build: str, binary_name: str, entry: str= "$@", other: str= "") -> str:
    """
    Creates the Docker run command for the given binary.
    :param irods_test_server: the iRODS server to create proxies to
    :param docker_build: the build name of the Docker image to run
    :param binary_name: the docker_build of the binary
    :param entry: the CMD entrypoint
    :param other: other flags to pass to Docker run
    :return: the created command
    """
    if irods_test_server.host == "localhost" or irods_test_server.host == "127.0.0.1":
        raise ValueError(
            "Cannot connect to iRODS test server running on localhost - address is not usable inside Docker container.")

    to_execute = "\"%s\" \"%s\"" % (binary_name.replace('"', '\\"'), entry.replace('"', '\\"'))
    user = irods_test_server.users[0]

    if isinstance(irods_test_server, ContainerisedIrodsServer):
        other = "--link %s:%s %s" % (irods_test_server.name, irods_test_server.name, other)
        irods_test_server.host = irods_test_server.name
        irods_test_server.port = 1247

    assert irods_test_server.host is not None
    assert isinstance(irods_test_server.port, int)

    return "docker run -i --rm " \
           "-e IRODS_USERNAME='%s' " \
           "-e IRODS_HOST='%s' " \
           "-e IRODS_PORT=%d " \
           "-e IRODS_ZONE='%s' " \
           "-e IRODS_PASSWORD='%s' " \
           "%s %s %s" \
           % (
               user.username,
               irods_test_server.host,
               irods_test_server.port,
               user.zone,
               user.password,
               other, docker_build, to_execute)
