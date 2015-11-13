import tempfile

from docker import Client
from docker.utils import kwargs_from_env

from testwithbaton.irods_test_server import create_irods_test_server


_IRODS_CONFIG_FILE_NAME = ".irodsEnv"


def create_client() -> Client:
    """
    Clients a Docker client.

    Will raise a `ConnectionError` if the Docker daemon is not running.
    :return: the Docker client
    """
    docker_environment = kwargs_from_env(assert_hostname=False)

    if "base_url" not in docker_environment:
        raise ConnectionError(
            "Cannot connect to Docker - is the Docker daemon running? `$DOCKER_HOST` should be set.")

    return Client(**kwargs_from_env(assert_hostname=False))




def create_baton_proxy_binaries() -> str:
    """
    TODO
    :return: directory... TOOD
    """
    file_handle, pathname = tempfile.mkstemp(suffix="baton-proxy")
    pass



    # docker run -it -v /home/you/.irods:/root/.irods -e _IRODS_PASSWORD="mypassword" wtsi-hgi/baton baton-get




docker_client = create_client()

irods_test_server = create_irods_test_server(docker_client)
# docker_client.start(irods_test_server)




#
# print(find_hostname(docker_client))



# irods_container, irods_port = create_irods_server_container(docker_client)
# docker_client.start(irods_container)
#
# sleep(10)
#
# # TODO: Ensure kill, regardless of exception
# docker_client.kill(irods_container)









