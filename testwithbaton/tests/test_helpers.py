import unittest

from testwithbaton.api import TestWithBatonSetup
from testwithbaton.helpers import SetupHelper
from testwithbaton.models import Metadata


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
        self.setup_helper.create_irods_file(file_name, file_contents=contents)

        self.assertIn(file_name, self.setup_helper.run_icommand("ils"))

    def test_create_irods_collection(self):
        collection_name = "collection"
        self.setup_helper.create_irods_collection(collection_name)

        self.assertIn("/%s" % collection_name, self.setup_helper.run_icommand("ils"))

    def test_add_irods_metadata_to_file(self):
        file_name = "filename"
        self.setup_helper.create_irods_file(file_name)

        metadata = Metadata("attribute", "value")
        self.setup_helper.add_irods_metadata_to_file(file_name, metadata)

        retrieved_metadata = self.setup_helper.run_icommand("imeta", ["ls", "-d", file_name])
        self.assertIn("attribute: %s" % metadata.attribute, retrieved_metadata)
        self.assertIn("value: %s" % metadata.value, retrieved_metadata)

    def tearDown(self):
        self.test_with_baton.tear_down()
