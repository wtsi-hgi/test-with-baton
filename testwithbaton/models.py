from typing import List


class IrodsUser:
    """
    TODO
    """
    def __init__(self, username: str, password: str, zone: str):
        self.username = username
        self.password = password
        self.zone = zone


class IrodsServer:
    """
    TODO
    """
    def __init__(self, container: dict, host: str, port: int, users: List[IrodsUser]):
        self.container = container
        self.host = host
        self.port = port
        self.users = users
