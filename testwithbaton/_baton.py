import logging

from docker import Client

from testwithbaton.models import BatonImage


def build_baton_docker(docker_client: Client, baton_docker_build: BatonImage):
    """
    Builds the baton Docker image.
    :param docker_client: the Docker client
    :param baton_docker_build: where the baton docker is built from
    """
    logging.info("Building baton Docker image - if this is not cached, it will take a few minutes")
    logging.debug("baton Docker build: %s" % baton_docker_build)
    # Note: reading the lines in this ways enforces that Python blocks - required
    for line in docker_client.build(tag=baton_docker_build.tag, path=baton_docker_build.path,
                                    dockerfile=baton_docker_build.docker_file, buildargs=baton_docker_build.build_args):
        logging.debug(line)
