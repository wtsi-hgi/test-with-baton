import os
import shutil
import subprocess
import tempfile
from typing import List

from hgicommon.collections import Metadata


class SetupHelper:
    """
    Helper for setting up tests.
    """
    def __init__(self, icommands_location: str):
        """
        Constructor.
        :param icommands_location: the location of the icommands that can be used to communicate with the iRODS server
        """
        self.icommands_location = icommands_location

    def create_data_object(self, file_name: str, file_contents: str= "") -> str:
        """
        Creates a test data object on iRODS with the given build_name and contents.
        :param file_name: the build_name of the file to create
        :param file_contents: the contents of the file to create
        :return: the path to the created file
        """
        if "/" in file_name:
            raise ValueError("File build_name cannot include '/'")

        # XXX: Using the default setup of Docker, the temp directory that Python uses cannot be mounted on Mac.
        # As a work around, mounting in the directory in which the test is running in.
        accesible_directory = os.path.dirname(os.path.realpath(__file__))
        temp_directory_path = tempfile.mkdtemp(prefix=".iput-", dir=accesible_directory)
        temp_file_path = os.path.join(temp_directory_path, file_name)
        os.chmod(temp_directory_path, 0o770)

        with open(temp_file_path, 'w+') as temp_file:
            temp_file.write(file_contents)
        os.chmod(temp_file_path, 0o770)

        self.run_icommand("iput", [temp_file_path])
        shutil.rmtree(temp_directory_path)

        return "%s/%s" % (self.run_icommand("ipwd"), file_name)

    def create_collection(self, collection_name: str) -> str:
        """
        Creates a test collection on iRODS with the given build_name and contents.
        :param collection_name: the build_name of the collection to create
        :return: the path to the created collection
        """
        if "/" in collection_name:
            raise ValueError("Collection build_name cannot include '/'")

        self.run_icommand("imkdir", [collection_name])

        return "%s/%s" % (self.run_icommand("ipwd"), collection_name)

    def add_metadata_to(self, location: str, metadata: Metadata):
        """
        Adds the given metadata to the entity at the given location in iRODS.
        :param location: the location to add metadata to (could correspond to a collection or data object)
        :param metadata: the metadata to add
        """
        type_flag = "-c" if self.is_collection(location) else "-d"

        for key, values in metadata.items():
            if not isinstance(values, list) and not isinstance(values, set):
                values = [values]
            assert type(values) != str
            for value in values:
                self.run_icommand("imeta", ["add", type_flag, location, key, str(value)])

    def is_collection(self, location: str) -> bool:
        """
        Checks whether the given location in iRODS is a collection.
        :param location: the location to check
        :return: whether there is a collection at the given location
        """
        listing = self.run_icommand("ils", [location])
        return ":" in listing

    def get_checksum(self, path: str) -> str:
        """
        Gets the checksum of the given data object on iRODS.
        :param path: the path to the data object
        :return: the checksum of the data object
        """
        checksum_out = self.run_icommand("ichksum", [path])
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
