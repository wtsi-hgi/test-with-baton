import unittest

from hgicommon.collections import Metadata

from testwithbaton.api import TestWithBatonSetup
from testwithbaton.helpers import SetupHelper


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

        metadata = Metadata({"attribute_1": ["value_1", "value_2"], "attribute_2": {"value_3", "value_4"},
                             "attribute_3": "value_5"})
        self.setup_helper.add_metadata_to(path, metadata)

        retrieved_metadata = self.setup_helper.run_icommand("imeta", ["ls", "-d", path])
        self.assertIn("attribute: attribute_1\nvalue: value_1", retrieved_metadata)
        self.assertIn("attribute: attribute_1\nvalue: value_2", retrieved_metadata)
        self.assertIn("attribute: attribute_2\nvalue: value_3", retrieved_metadata)
        self.assertIn("attribute: attribute_2\nvalue: value_4", retrieved_metadata)
        self.assertIn("attribute: attribute_3\nvalue: value_5", retrieved_metadata)

    def test_add_metadata_to_collection(self):
        path = self.setup_helper.create_collection("collection")

        metadata = Metadata({"attribute_1": ["value_1", "value_2"], "attribute_2": {"value_3", "value_4"},
                             "attribute_3": "value_5"})
        self.setup_helper.add_metadata_to(path, metadata)

        retrieved_metadata = self.setup_helper.run_icommand("imeta", ["ls", "-c", path])
        self.assertIn("attribute: attribute_1\nvalue: value_1", retrieved_metadata)
        self.assertIn("attribute: attribute_1\nvalue: value_2", retrieved_metadata)
        self.assertIn("attribute: attribute_2\nvalue: value_3", retrieved_metadata)
        self.assertIn("attribute: attribute_2\nvalue: value_4", retrieved_metadata)
        self.assertIn("attribute: attribute_3\nvalue: value_5", retrieved_metadata)

    def test_get_checksum(self):
        file_name = "filename"
        path = self.setup_helper.create_data_object(file_name, "abc")
        self.assertEquals(self.setup_helper.get_checksum(path), "900150983cd24fb0d6963f7d28e17f72")

    def tearDown(self):
        self.test_with_baton.tear_down()
