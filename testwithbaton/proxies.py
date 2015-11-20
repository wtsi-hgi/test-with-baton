import logging
import os
import tempfile
from typing import List, Tuple, Optional
from docker import Client

from testwithbaton.models import IrodsServer

_SHEBANG = "#!/usr/bin/env bash"

_BATON_BINARIES = ["baton", "baton-metaquery", "baton-get", "baton-chmod", "baton-list", "baton-metamod"]
_ICOMMAND_BINARIES = ["ibun", "icd", "ichksum", "ichmod", "icp", "idbug", "ienv", "ierror", "iexecmd", "iexit", "ifsck",
                      "iget", "igetwild", "ihelp", "iinit", "ilocate", "ils", "ilsresc", "imcoll", "imiscsvrinfo",
                      "imkdir", "imv", "ipasswd", "iphybun", "iphymv", "ips", "iput", "ipwd", "iqdel", "iqmod",
                      "iqstat", "iquest", "iquota", "ireg", "irepl", "irm", "irmtrash", "irsync", "irule", "iscan",
                      "isysmeta", "itrim", "iuserinfo", "ixmsg", "izonereport", "imeta"]

# TODO: These should be settings?
_BATON_DOCKER_TAG = "wtsi-hgi/baton:0.16.1"
_BATON_DOCKER_FILE = "0.16.1/irods-3.3.1/Dockerfile"
_BATON_DOCKER_REPOSITORY = "github.com/wtsi-hgi/docker-baton.git"


def build_baton_docker(docker_client: Client):
    """
    Builds the baton Docker image.
    :param docker_client: the Docker client
    """
    logging.info("Building baton test Docker image - if this is not cached, it will take a few minutes")
    # Note: reading the lines in this ways enforces that Python blocks - required
    response = [line for line in docker_client.build(tag=_BATON_DOCKER_TAG, path=_BATON_DOCKER_REPOSITORY, dockerfile=_BATON_DOCKER_FILE)]
    logging.debug(response)


def create_baton_proxy_binaries(irods_test_server: IrodsServer) -> str:
    """
    Creates binaries that act as proxies to the baton binaries in the baton Docker. Allows realistic baton installation,
    where binaries are called from a directory.
    :return: the directory containing the baton proxy binaries
    """
    return _create_proxy_binaries(irods_test_server, "baton-proxies-", _BATON_BINARIES)


def create_icommands_proxy_binaries(irods_test_server: IrodsServer) -> str:
    """
    Creates binaries that act as proxies to the icommands in the baton Docker.
    :return: the directory containing the icommand proxy binaries
    """
    return _create_proxy_binaries(irods_test_server, "icommands-proxies-", _ICOMMAND_BINARIES)


def _create_proxy_binaries(irods_test_server: IrodsServer, directory_prefix: str, binaries: List[str]) -> str:
    """
    Create proxies to the given binaries.
    :param irods_test_server: the iRODS server to use
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

            if binary == "iput":
                # FIXME: allow other flags, handle no $1 givne
                file.write("""
                        cd $(dirname "$1")
                        mountDirectory=$PWD
                        fileName=$(basename "$1")
                        %s
                """ % (
                    _create_docker_run_command(irods_test_server, binary, other="-v \"$mountDirectory\":/tmp/input:ro", entry="\"/tmp/input/$fileName\"")
                ))
            else:
                file.write("%s\n" % _create_docker_run_command(irods_test_server, binary))
        os.chmod(file_path, 0o770)

    return temp_directory


def _create_docker_run_command(irods_test_server: IrodsServer, binary_name: str, entry: str= "$@", other: str= "") -> str:
    """
    Creates the Docker run command for the given binary.
    :param irods_test_server: the iRODS server to use
    :param binary_name: the name of the binary
    :param entry: the CMD entrypoint
    :param other: other flags to pass to Docker run
    :return: the created command
    """
    to_execute = "\"%s\" \"%s\"" % (binary_name.replace('"', '\\"'), entry.replace('"', '\\"'))
    user = irods_test_server.users[0]

    return "docker run -i --rm -e IRODS_USERNAME='%s' -e IRODS_HOST='%s' -e IRODS_PORT=%d -e IRODS_ZONE='%s' -e IRODS_PASSWORD='%s' %s %s %s" \
           % (user.username, irods_test_server.host, irods_test_server.port, user.zone, user.password, other, _BATON_DOCKER_TAG, to_execute)


