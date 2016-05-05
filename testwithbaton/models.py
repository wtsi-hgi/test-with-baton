from typing import List

import semantic_version
from hgicommon.models import Model

# Import from semantic version library
Version = semantic_version.Version


class Container:
    """
    Model of a Docker container.
    """
    def __init__(self):
        self.native_object = None
        self.name = None


class IrodsUser(Model):
    """
    Model of an iRODS user.
    """
    def __init__(self, username: str, zone: str, password: str=None, admin=False):
        self.username = username
        self.password = password
        self.zone = zone
        self.admin = admin


class IrodsServer(Model):
    """
    Model of an iRODS server.
    """
    def __init__(self, host: str=None, port: int=None, users: List[IrodsUser]=None, version: Version=None):
        super().__init__()
        self.host = host
        self.port = port
        self.users = [] if users is None else users     # type: List[IrodsUser]
        self.version = version


class ContainerisedIrodsServer(IrodsServer, Container):
    """
    Model of an iRODS server that runs in a container.
    """
    def __init__(self):
        super().__init__()


class BatonImage(Model):
    """
    Model of a baton Docker build.
    """
    def __init__(self, tag: str, path: str=None, docker_file: str=None,
                 build_args: dict=None):
        self.tag = tag
        self.path = path
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
