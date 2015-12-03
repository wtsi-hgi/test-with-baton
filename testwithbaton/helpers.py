import os
import shutil
import subprocess
import tempfile
from typing import List

from hgicommon.collections import Metadata
from hgicommon.models import File


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

    def create_irods_file(self, file_name: str, file_contents: str="") -> File:
        """
        Creates a test data object file on iRODS with the given name and contents.
        :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
        :param file_name: the name of the file to create
        :param file_contents: the contents of the file to create
        :return: the file created
        """
        if "/" in file_name:
            raise ValueError("File name cannot include '/'")

        # XXX: for some reason Docker was having problems mounting a directory in the temp directory that Python uses. As
        # a work around, mounting in the directory in which the test is running in.
        accesible_directory = os.path.dirname(os.path.realpath(__file__))
        temp_directory_path = tempfile.mkdtemp(prefix=".iput-", dir=accesible_directory)
        temp_file_path = os.path.join(temp_directory_path, file_name)
        os.chmod(temp_directory_path, 0o770)

        with open(temp_file_path, 'w+') as temp_file:
            temp_file.write(file_contents)
        os.chmod(temp_file_path, 0o770)

        self.run_icommand("iput", [temp_file_path])
        shutil.rmtree(temp_directory_path)

        return File(self.run_icommand("ipwd"), file_name)

    def create_irods_collection(self, collection_name: str) -> File:
        """
        Creates a test collection on iRODS with the given name and contents.
        :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
        :param collection_name: the name of the collection to create
        :return: the file created
        """
        if "/" in collection_name:
            raise ValueError("Collection name cannot include '/'")

        self.run_icommand("imkdir", [collection_name])

        return File(self.run_icommand("ipwd"), collection_name)

    def add_metadata_to_file(self, file: File, metadata: Metadata):
        """
        Adds the given metadata to a file on iRODS.
        :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
        :param file: the file to add metadata to
        :param metadata: the metadata to add
        """
        for key, values in metadata.items():
            if not isinstance(values, list):
                values = [values]
            for value in values:
                self.run_icommand("imeta", ["add", "-d", file.file_name, key, value])

    def get_checksum(self, file: File) -> str:
        """
        Gets the checksum of the given file on iRODS.
        :param file: the file to get the checksum for
        :return: the checksum of the file
        """
        checksum_out = self.run_icommand("ichksum", [file.directory + '/' + file.file_name])
        return checksum_out.split('\n')[0].rsplit(' ', 1)[-1]

    def run_icommand(self, icommand_binary: str, command_arguments: List[str]=None) -> str:
        """
        Executes the given icommand binary with any arguments, returning the stdout as a string and raising an
        exception if stderr is written to.
        :param icommand_binary: the binary to execute
        :param command_arguments: command arguments
        :return: the output written to stdout by the icommand that was executed
        """
        binary_path = os.path.join(self.icommands_location, icommand_binary)
        arguments = [binary_path]
        if command_arguments is not None:
            arguments += command_arguments

        process = subprocess.Popen(
            arguments, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        out, error = process.communicate()

        if len(error) != 0:
            raise RuntimeError("%s:\nError: %s\nOutput: %s" % (arguments, error, out))

        return out.decode("utf-8").rstrip()
