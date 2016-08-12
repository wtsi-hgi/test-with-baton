from hgicommon.models import Model


class BatonImage(Model):
    """
    Model of a baton Docker build.
    """
    def __init__(self, tag: str, path: str=None, docker_file: str=None, build_args: dict=None):
        self.tag = tag
        self.path = path
        self.docker_file = docker_file
        self.build_args = build_args
