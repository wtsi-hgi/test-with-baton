from typing import List

from hgicommon.models import Model


class IrodsUser(Model):
    """
    Model of an iRODS user.
    """
    def __init__(self, username: str, password: str, zone: str, admin=False):
        self.username = username
        self.password = password
        self.zone = zone
        self.admin = admin


class IrodsServer(Model):
    """
    Model of an iRODS server.
    """
    def __init__(self, host: str, port: int, users: List[IrodsUser]):
        if not isinstance(port, int):
            raise ValueError("Port number must be an integer: `%s` given" % port.__class__)
        self.host = host
        self.port = port
        self.users = users


class ContainerisedIrodsServer(IrodsServer):
    """
    Model of an iRODS server that runs in a container.
    """
    def __init__(self, container: dict, host: str, port: int, users: List[IrodsUser]):
        super(ContainerisedIrodsServer, self).__init__(host, port, users)
        self.container = container


class BatonDockerBuild(Model):
    """
    Model of a baton Docker build.
    """
    def __init__(self, path: str, build_name: str, docker_file: str="Dockerfile", build_args: dict=()):
        self.path = path
        self.build_name = build_name
        self.docker_file = docker_file
        self.build_args = build_args


class IrodsResource(Model):
    """
    Model of a iRODS server resource.
    """
    def __init__(self, name: str, host: str, location: str):
        self.name = name
        self.host = host
        self.location = location