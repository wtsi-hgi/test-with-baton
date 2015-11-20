from typing import List, Any


class IrodsUser:
    """
    Model of an iRODS user.
    """
    def __init__(self, username: str, password: str, zone: str):
        self.username = username
        self.password = password
        self.zone = zone


class IrodsServer:
    """
    Model of an iRODS server.
    """
    def __init__(self, container: dict, host: str, port: int, users: List[IrodsUser]):
        self.container = container
        self.host = host
        self.port = port
        self.users = users


class Metadata:
    """
    Model of a unit of metadata
    """
    def __init__(self, attribute: str, value: Any):
        self.attribute = attribute
        self.value = value
