import atexit
import logging
import os
import shutil
import tempfile
from abc import ABCMeta, abstractmethod
from typing import Set
from uuid import uuid4

from docker.errors import NotFound

from testwithbaton._common import create_client
from testwithbaton.models import IrodsServer, ContainerisedIrodsServer

_SHEBANG = "#!/usr/bin/env bash"
_FAIL_SETTINGS = "set -eu -o pipefail"


class ProxyController(metaclass=ABCMeta):
    """
    Controller for proxy binaries that execute commands in a transparent Docker container.
    """
    @staticmethod
    def _reduce_whitespace(commands: str) -> str:
        """
        Reduces the whitespace in the given command.
        :param commands: the command to reduce whitespace from
        :return: command with reduced whitespace
        """
        commands = commands.replace("    ", "")
        commands = commands.strip()
        return commands

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
        self.cached_container_name = "binary-container-%s" % uuid4()
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

        docker_client = create_client()
        try:
            docker_client.remove_container(self.cached_container_name, force=True)
        except NotFound:
            """ Not bothered if the container had not yet been created """

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
        and fail settings
        """
        file_path = os.path.join(directory, binary_to_execute_in_docker)
        with open(file_path, 'w') as file:
            file.write("%s\n" % _SHEBANG)
            file.write("%s\n" % _FAIL_SETTINGS)
            if alternate_commands:
                file.write(alternate_commands)
            else:
                file.write("%s\n" % self._create_proxy_commands(binary_to_execute_in_docker))
        os.chmod(file_path, 0o770)

    def _create_proxy_commands(self, binary_to_execute_in_docker: str, arguments: str= "\"$@\"", flags: str= "") -> str:
        """
        Creates the commands that the proxy binary should contain to transparently run the given binary inside Docker.
        :param binary_to_execute_in_docker: the binary that is to be run inside Docker
        :param arguments: the CMD entrypoint (i.e. the command executed inside the container)
        :param flags: other flags to use in Docker run (will not use pre-running container if set)
        :return: the created command
        """
        if self._irods_test_server.host == "localhost" or self._irods_test_server.host == "127.0.0.1":
            raise ValueError("Cannot connect to iRODS test server running on localhost - "
                             "address is not usable inside Docker container.")

        binary_to_execute_in_docker = binary_to_execute_in_docker.replace('"', '\\"')
        to_execute = "\"%s\" %s" % (binary_to_execute_in_docker, arguments)

        other_flags_set = flags != ""
        if isinstance(self._irods_test_server, ContainerisedIrodsServer):
            flags = "--link %s:%s %s" % (self._irods_test_server.name, self._irods_test_server.name, flags)
            # TODO: Changing this is probably wrong
            self._irods_test_server.host = self._irods_test_server.name
            self._irods_test_server.port = 1247

        assert self._irods_test_server.host is not None
        assert isinstance(self._irods_test_server.port, int)

        if other_flags_set:
            return self._create_docker_run_command(to_execute, flags)
        else:
            flags = "--name %s -d %s -i" % (self.cached_container_name, flags)
            return ProxyController._reduce_whitespace("""
                isRunning() {
                    [ $(docker ps -f name=%(uuid)s | wc -l | awk '{print $1}') -eq 2 ]
                }

                if ! isRunning;
                then
                    startIfNotRunning() {
                        if ! isRunning
                        then
                            %(container_setup)s > /dev/null
                        fi
                    }
                    lock=".%(uuid)s.lock"
                    if type flock > /dev/null 2>&1
                    then
                        # Linux
                        (
                            flock 10
                            startIfNotRunning
                            rm -f /tmp/${lock}
                        ) 10> /tmp/${lock}
                    elif type lockfile > /dev/null 2>&1
                    then
                        # Mac
                        lockfile /tmp/${lock}
                        startIfNotRunning
                        rm -f /tmp/${lock}
                    else
                        # No supported lock functionality - blindly try to start it and ignore any error
                        set +e
                        startIfNotRunning 2> /dev/null
                        set -e
                    fi
                fi

                docker exec -i %(uuid)s %(to_execute)s
            """ % {
                "uuid": self.cached_container_name,
                "container_setup": self._create_docker_run_command("bash", flags),
                "to_execute": to_execute
            })

    def _create_docker_run_command(self, command: str, other: str="") -> str:
        """
        Creates a command to run the given entry inside a Docker container.
        :param command: the CMD entrypoint (i.e. the command executed inside the container)
        :param other: other flags to use in Docker run
        :return: the created command
        """
        user = self._irods_test_server.users[0]

        return ProxyController._reduce_whitespace("""
                docker run \
                    -e IRODS_HOST='%(host)s' \
                    -e IRODS_PORT=%(port)d \
                    -e IRODS_ZONE='%(zone)s' \
                    -e IRODS_USERNAME='%(username)s' \
                    -e IRODS_PASSWORD='%(password)s' \
                    %(other)s \
                    %(image)s \
                    %(command)s
        """ % {
            "host": self._irods_test_server.host,
            "port": self._irods_test_server.port,
            "zone": user.zone,
            "username": user.username,
            "password": user.password,
            "other": other,
            "image": self._docker_image,
            "command": command
        })


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
        container_directory = self._create_temp_container_directory("icommand-proxies-")
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
        # FIXME: Issue mounting temp directory leads to use of current directory, which is not good!
        docker_run_command = self._create_proxy_commands("iput", arguments="\"/tmp/input/$fileName\"",
                                                         flags="-v \"$mountDirectory\":/tmp/input:ro -i")
        commands = ProxyController._reduce_whitespace("""
            cd $(dirname "$1")
            mountDirectory=$PWD
            fileName=$(basename "$1")
            %s
        """ % docker_run_command)

        self._create_proxy(container_directory, "iput", alternate_commands=commands)
