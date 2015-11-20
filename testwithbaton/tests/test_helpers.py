import os
import unittest

import subprocess

from typing import List

from testwithbaton.api import TestWithBatonSetup
from testwithbaton.helpers import create_irods_file, create_irods_collection, add_irods_metadata_to_file
from testwithbaton.models import Metadata


class TestHelpers(unittest.TestCase):
    """
    Tests on helper methods.
    """
    def setUp(self):
        self.test_with_baton = TestWithBatonSetup()
        self.test_with_baton.setup()

    def test_create_irods_file(self):
        file_name = "filename"
        contents = "Test file contents"
        create_irods_file(self.test_with_baton.icommands_location, file_name, file_contents=contents)

        self.assertIn(file_name, self._run_icommand("ils"))

    def test_create_irods_collection(self):
        collection_name = "collection"
        create_irods_collection(self.test_with_baton.icommands_location, collection_name)

        self.assertIn("/%s" % collection_name, self._run_icommand("ils"))

    def test_add_irods_metadata_to_file(self):
        file_name = "filename"
        create_irods_file(self.test_with_baton.icommands_location, file_name)

        metadata = Metadata("attribute", "value")
        add_irods_metadata_to_file(self.test_with_baton.icommands_location, file_name, metadata)

        retrieved_metadata = self._run_icommand("imeta", ["ls", "-d", file_name])
        self.assertIn("attribute: %s" % metadata.attribute, retrieved_metadata)
        self.assertIn("value: %s" % metadata.value, retrieved_metadata)

    def tearDown(self):
        self.test_with_baton.tear_down()

    def _run_icommand(self, binary: str, command_arguments: List[str]=None) -> str:
        """
        Executes the given icommand binary with any arguments, returning the stdout as a string and raising an exception
        if stderr is not `None`.
        :param binary: the binary to execute
        :param command_arguments: command arguments
        :return: the output written to stdout by the icommand that was excuted
        """
        binary_path = os.path.join(self.test_with_baton.icommands_location, binary)
        arguments = [binary_path]
        if command_arguments is not None:
            arguments += command_arguments

        process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, error = process.communicate()

        if error is not None:
            raise RuntimeError(error)

        return out.decode("utf-8").rstrip()