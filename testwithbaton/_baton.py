import logging

from docker import Client

from testwithbaton.models import BatonDockerBuild


def build_baton_docker(docker_client: Client, baton_docker_build: BatonDockerBuild):
    """
    Builds the baton Docker image.
    :param docker_client: the Docker client
    :param baton_docker_build: the Git path from which the baton Docker is built
    """
    logging.info("Building baton test Docker image - if this is not cached, it will take a few minutes")
    logging.debug("baton Docker build: %s" % baton_docker_build)
    # Note: reading the lines in this ways enforces that Python blocks - required
    response = [line for line in docker_client.build(tag=baton_docker_build.tag,
                                                     path=baton_docker_build.path,
                                                     dockerfile=baton_docker_build.docker_file,
                                                     buildargs=baton_docker_build.build_args)]
    logging.debug(response)
