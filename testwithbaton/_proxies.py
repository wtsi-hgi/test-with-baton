import atexit
import logging
import os
import shutil
import tempfile
from abc import ABCMeta, abstractmethod
from typing import Set

from testwithbaton.models import IrodsServer, ContainerisedIrodsServer

_SHEBANG = "#!/usr/bin/env bash"


class ProxyController(metaclass=ABCMeta):
    """
    Controller for proxy binaries that execute commands in a transparent Docker container.
    """
    @abstractmethod
    def create_proxy_binaries(self) -> str:
        """
        Creates the proxy binaries that this controller manager. The binaries act as proxies to the binaries that are
        executed in a Docker container.
        :return: the directory containing the proxies
        """

    def __init__(self, irods_test_server: IrodsServer, docker_image: str):
        """
        Constructor.
        :param irods_test_server: the iRODS server that the proxied binaries use
        :param docker_image: the name (docker-py's "tag") of the Docker image that the proxied binaries are executed
        within
        """
        self._irods_test_server = irods_test_server
        self._docker_image = docker_image
        self._temp_directories = set()     # type: Set[str]
        atexit.register(self.tear_down)

    def tear_down(self):
        """
        Tears down the controller.
        """
        while len(self._temp_directories) > 0:
            directory = self._temp_directories.pop()
            shutil.rmtree(directory, ignore_errors=True)

    def _create_temp_container_directory(self, directory_prefix: str="") -> str:
        """
        Creates a temp directory that can contain binary proxies. Directories created via this method are registered
        for automatic removal on tear down.
        :param directory_prefix: optional prefix for the directory name
        :return: path to the temp directory
        """
        temp_directory = tempfile.mkdtemp(prefix=directory_prefix)
        self._temp_directories.add(temp_directory)
        logging.debug("Created temp directory for proxy binaries: %s" % temp_directory)
        return temp_directory

    def _create_proxy(self, directory: str, binary_to_execute_in_docker: str, alternate_commands: str=None):
        """
        Creates a binary that proxies a call to a binary executed in Docker. Created binary looks like the binary that
        is to be executed in Docker, hence the use of Docker is transparent.

        Custom alternate commands are required to support the use of commands that require files from the host machine.
        :param directory: the directory to create the binary in
        :param binary_to_execute_in_docker: the binary that is to be executed in docker
        :param alternate_commands: alternate command to write to the proxy executable. Will be written after the shebang
        """
        file_path = os.path.join(directory, binary_to_execute_in_docker)
        with open(file_path, 'w') as file:
            file.write("%s\n" % _SHEBANG)
            if alternate_commands:
                file.write(alternate_commands)
            else:
                file.write("%s\n" % self._create_docker_run_command(binary_to_execute_in_docker))
        os.chmod(file_path, 0o770)

    def _create_docker_run_command(self, binary_name: str, entry: str="$@", other: str="") -> str:
        """
        Creates the Docker run command for the given binary.
        :param binary_name: the docker_build of the binary
        :param entry: the CMD entrypoint
        :param other: other flags to pass to Docker run
        :return: the created command
        """
        if self._irods_test_server.host == "localhost" or self._irods_test_server.host == "127.0.0.1":
            raise ValueError("Cannot connect to iRODS test server running on localhost - "
                             "address is not usable inside Docker container.")

        to_execute = "\"%s\" \"%s\"" % (binary_name.replace('"', '\\"'), entry.replace('"', '\\"'))
        user = self._irods_test_server.users[0]

        if isinstance(self._irods_test_server, ContainerisedIrodsServer):
            other = "--link %s:%s %s" % (self._irods_test_server.name, self._irods_test_server.name, other)
            self._irods_test_server.host = self._irods_test_server.name
            self._irods_test_server.port = 1247

        assert self._irods_test_server.host is not None
        assert isinstance(self._irods_test_server.port, int)

        # docker ps -f <name>

        return "docker run -i --rm " \
               "-e IRODS_USERNAME='%s' " \
               "-e IRODS_HOST='%s' " \
               "-e IRODS_PORT=%d " \
               "-e IRODS_ZONE='%s' " \
               "-e IRODS_PASSWORD='%s' " \
               "%s %s %s" \
               % (
                   user.username,
                   self._irods_test_server.host,
                   self._irods_test_server.port,
                   user.zone,
                   user.password,
                   other, self._docker_image, to_execute)


class BatonProxyController(ProxyController):
    """
    Controller for baton proxy binaries that execute baton commands in a transparent Docker container.
    """
    _BATON_BINARIES = {"baton", "baton-metaquery", "baton-get", "baton-chmod", "baton-list", "baton-metamod",
                       "baton-specificquery"}

    def create_proxy_binaries(self) -> str:
        container_directory = self._create_temp_container_directory("baton-proxies-")
        for binary in BatonProxyController._BATON_BINARIES:
            self._create_proxy(container_directory, binary)
        return container_directory


class ICommandProxyController(ProxyController):
    """
    Controller for icommands proxy binaries that execute icommands in a transparent Docker container.
    """
    _ICOMMAND_BINARIES = {"ibun", "icd", "ichksum", "ichmod", "icp", "idbug", "ienv", "ierror", "iexecmd", "iexit",
                          "ifsck", "iget", "igetwild", "ihelp", "iinit", "ilocate", "ils", "ilsresc", "imcoll",
                          "imiscsvrinfo", "imkdir", "imv", "ipasswd", "iphybun", "iphymv", "ips", "iput", "ipwd",
                          "iqdel", "iqmod", "iqstat", "iquest", "iquota", "ireg", "irepl", "irm", "irmtrash", "irsync",
                          "irule", "iscan", "isysmeta", "itrim", "iuserinfo", "ixmsg", "izonereport", "imeta", "iadmin"}

    def create_proxy_binaries(self) -> str:
        container_directory = self._create_temp_container_directory("baton-proxies-")
        for binary in ICommandProxyController._ICOMMAND_BINARIES - {"iput"}:
            self._create_proxy(container_directory, binary)
        self._create_iput_proxy_binary(container_directory)
        return container_directory

    def _create_iput_proxy_binary(self, container_directory: str):
        """
        Creates proxy binary for `iput`.
        :param container_directory: the icommand proxy binary container
        """
        # FIXME: allow other flags, handle no $1 given
        docker_run_command = self._create_docker_run_command("iput", other="-v \"$mountDirectory\":/tmp/input:ro",
                                                             entry="\"/tmp/input/$fileName\"")
        commands = """
                cd $(dirname "$1")
                mountDirectory=$PWD
                fileName=$(basename "$1")
                %s
        """ % docker_run_command

        self._create_proxy(container_directory, "iput", alternate_commands=commands)
