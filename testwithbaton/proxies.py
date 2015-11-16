import logging
import os
import tempfile

from docker import Client
from typing import List

from testwithbaton.irods_server import create_irods_server_connection_settings_volume
from testwithbaton.models import IrodsServer


_BATON_BINARIES = ["baton", "baton-metaquery", "baton-get", "baton-chmod", "baton-list", "baton-metamod"]
_ICOMMAND_BINARIES = ["ibun", "icd", "ichksum", "ichmod", "icp", "idbug", "ienv", "ierror", "iexecmd", "iexit", "ifsck",
                      "iget", "igetwild", "ihelp", "iinit", "ilocate", "ils", "ilsresc", "imcoll", "imiscsvrinfo",
                      "imkdir", "imv", "ipasswd", "iphybun", "iphymv", "ips", "iput", "ipwd", "iqdel", "iqmod",
                      "iqstat", "iquest", "iquota", "ireg", "irepl", "irm", "irmtrash", "irsync", "irule", "iscan",
                      "isysmeta", "itrim", "iuserinfo", "ixmsg", "izonereport"]

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
    return create_proxy_binaries(irods_test_server, "baton-proxies-", _BATON_BINARIES)


def create_icommands_proxy_binaries(irods_test_server: IrodsServer) -> str:
    """
    Creates binaries that act as proxies to the icommands in the baton Docker.
    :return: the directory containing the icommand proxy binaries
    """
    return create_proxy_binaries(irods_test_server, "icommands-proxies-", _ICOMMAND_BINARIES)


def create_proxy_binaries(irods_test_server: IrodsServer, directory_prefix: str, binaries: List[str]) -> str:
    """
    TODO
    :param irods_test_server:
    :param directory_prefix:
    :param binaries:
    :return: the directory containing the proxy binaries
    """
    temp_directory = tempfile.mkdtemp(prefix=directory_prefix)
    logging.debug("Created temp directory for proxy binaries: %s" % temp_directory)

    user = irods_test_server.users[0]
    # Create proxies
    for binary in binaries:
        file_path = os.path.join(temp_directory, binary)
        file = open(file_path, 'w')
        file.write("docker run -it -e IRODS_USERNAME=%s -e IRODS_HOST=%s -e IRODS_PORT=%d -e IRODS_ZONE=%s -e IRODS_PASSWORD='%s' %s %s $@"
                   % (user.username, irods_test_server.host, irods_test_server.port, user.zone, user.password, _BATON_DOCKER_TAG, binary))
        file.close()
        os.chmod(file_path, 0o770)

    return temp_directory