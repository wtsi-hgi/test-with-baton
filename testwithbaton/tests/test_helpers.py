import unittest

from hgicommon.collections import Metadata

from testwithbaton.api import TestWithBatonSetup
from testwithbaton.helpers import SetupHelper

_TEST_METADATA = Metadata({"attribute_1": ["value_1", "value_2"], "attribute_2": ["value_3", "value_4"],
                             "attribute_3": "value_5"})


class TestSetupHelper(unittest.TestCase):
    """
    Tests for `SetupHelper`.
    """
    def setUp(self):
        self.test_with_baton = TestWithBatonSetup()
        self.test_with_baton.setup()
        self.setup_helper = SetupHelper(self.test_with_baton.icommands_location)

    def test_run_icommand(self):
        ils = self.setup_helper.run_icommand("ils")

        self.assertTrue(ils.startswith("/"))
        self.assertTrue(ils.endswith(":"))

    def test_create_data_object(self):
        file_name = "filename"
        contents = "Test file contents"
        path = self.setup_helper.create_data_object(file_name, file_contents=contents)

        self.setup_helper.run_icommand("icd", [path.rsplit('/', 1)[-1]])
        self.assertIn(file_name, self.setup_helper.run_icommand("ils"))

    def test_create_data_object_with_file_path_opposed_to_file_name(self):
        self.assertRaises(ValueError, self.setup_helper.create_data_object, "/test")

    def test_create_collection(self):
        collection_name = "collection"
        path = self.setup_helper.create_collection(collection_name)

        self.setup_helper.run_icommand("icd", [path.rsplit('/', 1)[-1]])
        self.assertIn(collection_name, self.setup_helper.run_icommand("ils"))

    def test_create_collection_with_collection_path_opposed_to_collection_name(self):
        self.assertRaises(ValueError, self.setup_helper.create_collection, "/test")

    def test_add_metadata_to_data_object(self):
        path = self.setup_helper.create_data_object("filename")

        self.setup_helper.add_metadata_to(path, _TEST_METADATA)

        retrieved_metadata = self.setup_helper.run_icommand("imeta", ["ls", "-d", path])
        self._assert_metadata_in_retrieved(_TEST_METADATA, retrieved_metadata)

    def test_add_metadata_to_collection(self):
        path = self.setup_helper.create_collection("collection")

        self.setup_helper.add_metadata_to(path, _TEST_METADATA)

        retrieved_metadata = self.setup_helper.run_icommand("imeta", ["ls", "-c", path])
        self._assert_metadata_in_retrieved(_TEST_METADATA, retrieved_metadata)

    def test_get_checksum(self):
        file_name = "filename"
        path = self.setup_helper.create_data_object(file_name, "abc")
        self.assertEquals(self.setup_helper.get_checksum(path), "900150983cd24fb0d6963f7d28e17f72")

    def tearDown(self):
        self.test_with_baton.tear_down()

    def _assert_metadata_in_retrieved(self, metadata: Metadata, retrieved_metadata: str):
        """
        Assert that the given metadata is in metadata retrieved via an `imeta` command.
        :param metadata: the metadata to expect
        :param retrieved_metadata: string representation of metadata, retrieved via an `imeta` command
        """
        for attribute in metadata:
            attribute_values = metadata[attribute]
            if not isinstance(attribute_values, list):
                attribute_values = [attribute_values]

            for value in attribute_values:
                print(value)
                self.assertIn("attribute: %s\nvalue: %s" % (attribute, value), retrieved_metadata)
