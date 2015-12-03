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

    def test_create_irods_file(self):
        file_name = "filename"
        contents = "Test file contents"
        file = self.setup_helper.create_irods_file(file_name, file_contents=contents)

        self.assertEquals(file.file_name, file_name)
        self.assertEquals(file.directory, self.setup_helper.run_icommand("ipwd"))
        self.assertIn(file_name, self.setup_helper.run_icommand("ils"))

    def test_create_irods_file_with_file_path_opposed_to_file_name(self):
        self.assertRaises(ValueError, self.setup_helper.create_irods_file, "/test")

    def test_create_irods_collection(self):
        collection_name = "collection"
        collection = self.setup_helper.create_irods_collection(collection_name)

        self.assertEquals(collection.file_name, collection_name)
        self.assertEquals(collection.directory, self.setup_helper.run_icommand("ipwd"))
        self.assertIn("/%s" % collection_name, self.setup_helper.run_icommand("ils"))

    def test_create_irods_collection_with_collection_path_opposed_to_collection_name(self):
        self.assertRaises(ValueError, self.setup_helper.create_irods_collection, "/test")

    def test_add_irods_metadata_to_file(self):
        file_name = "filename"
        file = self.setup_helper.create_irods_file(file_name)

        metadata = Metadata({"attribute_1": ["value_1", "value_2"], "attribute_2": "value_3"})
        self.setup_helper.add_metadata_to_file(file, metadata)

        retrieved_metadata = self.setup_helper.run_icommand("imeta", ["ls", "-d", file_name])
        self.assertIn("attribute: attribute_1\nvalue: value_1", retrieved_metadata)
        self.assertIn("attribute: attribute_1\nvalue: value_2", retrieved_metadata)
        self.assertIn("attribute: attribute_2\nvalue: value_3", retrieved_metadata)

    def test_get_checksum(self):
        file_name = "filename"
        file = self.setup_helper.create_irods_file(file_name, "abc")
        self.assertEquals(self.setup_helper.get_checksum(file), "900150983cd24fb0d6963f7d28e17f72")

    def tearDown(self):
        self.test_with_baton.tear_down()
