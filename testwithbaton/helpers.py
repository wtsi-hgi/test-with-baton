import os
import shutil
import subprocess
import tempfile
from typing import List, Tuple, Union
from uuid import uuid4

from hgicommon.collections import Metadata

from testwithbaton.models import IrodsResource


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

    def create_data_object(self, name: str, contents: str= "") -> str:
        """
        Creates a test data object on iRODS with the given name and contents.
        :param name: the nane of the file to create
        :param contents: the contents of the file to create
        :return: the path to the created file
        """
        if "/" in name:
            raise ValueError("File name cannot include '/'")

        # XXX: Using the default setup of Docker, the temp directory that Python uses cannot be mounted on Mac.
        # As a work around, mounting in the directory in which the test is running in.
        accesible_directory = os.path.dirname(os.path.realpath(__file__))
        temp_directory_path = tempfile.mkdtemp(prefix=".iput-", dir=accesible_directory)
        temp_file_path = os.path.join(temp_directory_path, name)
        os.chmod(temp_directory_path, 0o770)

        with open(temp_file_path, 'w+') as temp_file:
            temp_file.write(contents)
        os.chmod(temp_file_path, 0o770)

        self.run_icommand("iput", [temp_file_path])
        shutil.rmtree(temp_directory_path)

        return "%s/%s" % (self.run_icommand("ipwd"), name)

    def replicate_data_object(self, path: str, replicate_to: Union[str, IrodsResource]):
        """
        Replicates the data object in the given path to the given resource.
        :param path: the path of the data object that is to be replicated
        :param replicate_to: the resource or name of the resource to which the data object should be replicated to
        """
        if isinstance(replicate_to, IrodsResource):
            replicate_to = replicate_to.name
        self.run_icommand("irepl", ["-R", replicate_to, path])

    def create_collection(self, name: str) -> str:
        """
        Creates a test collection on iRODS with the given name and contents.
        :param name: the name of the collection to create
        :return: the path to the created collection
        """
        if "/" in name:
            raise ValueError("Collection name cannot include '/'")

        self.run_icommand("imkdir", [name])

        return "%s/%s" % (self.run_icommand("ipwd"), name)

    def add_metadata_to(self, path: str, metadata: Metadata):
        """
        Adds the given metadata to the entity at the given path in iRODS.
        :param path: the path to add metadata to (could correspond to a collection or data object)
        :param metadata: the metadata to add
        """
        type_flag = "-c" if self.is_collection(path) else "-d"

        for key, values in metadata.items():
            if not isinstance(values, list) and not isinstance(values, set):
                values = [values]
            assert type(values) != str
            for value in values:
                self.run_icommand("imeta", ["add", type_flag, path, key, str(value)])

    def is_collection(self, path: str) -> bool:
        """
        Checks whether the given path in iRODS is a collection.
        :param path: the path to check
        :return: whether there is a collection at the given path
        """
        listing = self.run_icommand("ils", [path])
        return ":" in listing

    def update_checksums(self, path: str):
        """
        Forces iRODS to update the checksums of all replicas of the data object with the path given/all data objects
        in the collection given (recursive).
        :param path: the path to the data object/collection
        """
        self.run_icommand("ichksum", ["-f", "-a", "-r", path])

    def get_checksum(self, path: str) -> str:
        """
        Gets the checksum of the most recently updated replica of a data object on iRODS.

        If not stored in iRODS, the checksum will be calculated and stored as an unavoidable side-effect.
        :param path: the path to the data object
        :return: the checksum of the data object
        """
        checksum_out = self.run_icommand("ichksum", [path])
        return checksum_out.split('\n')[0].rsplit(' ', 1)[-1]

    def create_replica_storage(self) -> IrodsResource:
        """
        Creates replica storage resource.
        :return: resource on which replicas can be stored
        """
        name = str(uuid4())
        location = "/tmp/%s" % name
        self.run_icommand(
                "iadmin", ["mkresc", "'%s'" % name, "'unix file system'", "cache", "localhost", "'%s'" % location])
        return IrodsResource(name, location)

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
