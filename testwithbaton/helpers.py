import os
import shutil
import subprocess
import tempfile
from typing import List

from testwithbaton.models import Metadata


def create_irods_file(icommands_location: str, file_name: str, file_contents: str= ""):
    """
    Creates a test data object file on iRODS with the given name and contents.
    :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
    :param file_name: the name of the file to create
    :param file_contents: the contents of the file to create
    """
    # XXX: for some reason Docker was having problems mounting a directory in the temp directory that Python uses. As
    # a work around, mounting in the directory in which the test is running in.
    accesible_directory = os.path.dirname(os.path.realpath(__file__))
    temp_directory_path = tempfile.mkdtemp(prefix=".iput-", dir=accesible_directory)
    temp_file_path = os.path.join(temp_directory_path, file_name)
    os.chmod(temp_directory_path, 0o770)

    with open(temp_file_path, 'w+') as temp_file:
        temp_file.write(file_contents)
    os.chmod(temp_file_path, 0o770)

    iput = os.path.join(icommands_location, "iput")
    _run([iput, temp_file_path])

    shutil.rmtree(temp_directory_path)


def create_irods_collection(icommands_location: str, collection_name: str):
    """
    Creates a test collection on iRODS with the given name and contents.
    :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
    :param collection_name: the name of the collection to create
    """
    imkdir = os.path.join(icommands_location, "imkdir")
    _run([imkdir, collection_name])


def add_irods_metadata_to_file(icommands_location: str, file: str, metadata: Metadata):
    """
    Adds the given metadata to a file on iRODS.
    :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
    :param file:
    :param metadata:
    :return:
    """
    imeta = os.path.join(icommands_location, "imeta")
    _run([imeta, "add", "-d", file, metadata.attribute, metadata.value])


def _run(arguments: List[str]):
    """
    Runs the given argument, raising an exception if anything is written to either stdout or sterror.
    :param arguments: the arguments to execute
    """
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, error = process.communicate(timeout=30)
    if error is not None or len(out) != 0:
        raise RuntimeError("%s:\nError: %s\nOutput: %s" % (arguments, error, out))
