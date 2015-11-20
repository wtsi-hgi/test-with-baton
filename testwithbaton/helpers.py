import os
import shutil
import subprocess
import tempfile
from typing import List

from testwithbaton.models import Metadata


class SetupHelper:
    """
    Helper for setting up tests.
    """
    def __init__(self, icommands_location: str):
        """
        Default constructor.
        :param icommands_location: TODO
        """
        self.icommands_location = icommands_location

    def create_irods_file(self, file_name: str, file_contents: str= ""):
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

        self.run_icommand("iput", [temp_file_path], error_if_stdout=True)

        shutil.rmtree(temp_directory_path)

    def create_irods_collection(self, collection_name: str):
        """
        Creates a test collection on iRODS with the given name and contents.
        :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
        :param collection_name: the name of the collection to create
        """
        self.run_icommand("imkdir", [collection_name], error_if_stdout=True)

    def add_irods_metadata_to_file(self, file: str, metadata: Metadata):
        """
        Adds the given metadata to a file on iRODS.
        :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
        :param file:
        :param metadata:
        """
        self.run_icommand("imeta", ["add", "-d", file, metadata.attribute, metadata.value], error_if_stdout=True)

    def run_icommand(self, icommand_binary: str, command_arguments: List[str]=None, error_if_stdout=False) -> str:
        """
        Executes the given icommand binary with any arguments, returning the stdout as a string and raising an
        exception if stderr is not `None`
        :param icommand_binary: the binary to execute
        :param command_arguments: command arguments
        :param error_if_stdout: whether to raise an exception if text on stdout (failure mode for some icommands)
        :return: the output written to stdout by the icommand that was excuted
        """
        binary_path = os.path.join(self.icommands_location, icommand_binary)
        arguments = [binary_path]
        if command_arguments is not None:
            arguments += command_arguments

        process = subprocess.Popen(
            arguments, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = process.communicate()

        if error is not None or (error_if_stdout and len(out) != 0):
            raise RuntimeError("%s:\nError: %s\nOutput: %s" % (arguments, error, out))

        return out.decode("utf-8").rstrip()
