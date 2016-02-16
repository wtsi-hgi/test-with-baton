import unittest

from hgicommon.collections import Metadata

from testwithbaton import TestWithBatonSetup
from testwithbaton.helpers import SetupHelper

_METADATA = Metadata(
        {"attribute_1": ["value_1", "value_2"], "attribute_2": ["value_3", "value_4"], "attribute_3": "value_5"})
_DATA_OBJECT_NAME = "data-object-name"


class TestSetupHelper(unittest.TestCase):
    """
    Tests for `SetupHelper`.
    """
    def setUp(self):
        self.test_with_baton = TestWithBatonSetup()
        self.test_with_baton.setup()
        self.setup_helper = SetupHelper(self.test_with_baton.icommands_location)

    def test_run_icommand(self):
        ils = self.setup_helper.run_icommand(["ils"])

        self.assertTrue(ils.startswith("/"))
        self.assertTrue(ils.endswith(":"))

    def test_create_data_object_with_path_opposed_to_name(self):
        self.assertRaises(ValueError, self.setup_helper.create_data_object, "/test")

    def test_create_data_object(self):
        contents = "Test contents"
        path = self.setup_helper.create_data_object(_DATA_OBJECT_NAME, contents=contents)

        self.setup_helper.run_icommand(["icd", path.rsplit('/', 1)[-1]])
        self.assertIn(_DATA_OBJECT_NAME, self.setup_helper.run_icommand(["ils"]))
        # FIXME: Not testing for contents

    def test_replicate_data_object(self):
        data_object_location = self.setup_helper.create_data_object(_DATA_OBJECT_NAME)
        resource = self.setup_helper.create_replica_storage()
        self.setup_helper.replicate_data_object(data_object_location, resource)

        collection_listing = self.setup_helper.run_icommand(["ils", "-l"])
        self.assertIn("1 %s" % resource.name[0:20], collection_listing)

    def test_create_collection(self):
        collection_name = "collection"
        path = self.setup_helper.create_collection(collection_name)

        self.setup_helper.run_icommand(["icd", path.rsplit('/', 1)[-1]])
        self.assertIn(collection_name, self.setup_helper.run_icommand(["ils"]))

    def test_create_collection_with_collection_path_opposed_to_collection_name(self):
        self.assertRaises(ValueError, self.setup_helper.create_collection, "/test")

    def test_add_metadata_to_data_object(self):
        path = self.setup_helper.create_data_object(_DATA_OBJECT_NAME)

        self.setup_helper.add_metadata_to(path, _METADATA)

        retrieved_metadata = self.setup_helper.run_icommand(["imeta", "ls", "-d", path])
        self._assert_metadata_in_retrieved(_METADATA, retrieved_metadata)

    def test_add_metadata_to_collection(self):
        path = self.setup_helper.create_collection("collection")

        self.setup_helper.add_metadata_to(path, _METADATA)

        retrieved_metadata = self.setup_helper.run_icommand(["imeta", "ls", "-c", path])
        self._assert_metadata_in_retrieved(_METADATA, retrieved_metadata)

    def test_update_checksums(self):
        path = self.setup_helper.create_data_object(_DATA_OBJECT_NAME, "abc")
        resource = self.setup_helper.create_replica_storage()
        self.setup_helper.replicate_data_object(_DATA_OBJECT_NAME, resource)

        # Asserting that checksum is not stored before now
        assert "900150983cd24fb0d6963f7d28e17f72" not in self.setup_helper.run_icommand(["ils", "-L", path])
        self.setup_helper.update_checksums(path)

        ils = self.setup_helper.run_icommand(["ils", "-L", path])
        self.assertEquals(ils.count("900150983cd24fb0d6963f7d28e17f72"), 2)

    def test_get_checksum(self):
        path = self.setup_helper.create_data_object(_DATA_OBJECT_NAME, "abc")
        self.assertEquals(self.setup_helper.get_checksum(path), "900150983cd24fb0d6963f7d28e17f72")

    def test_create_replica_storage(self):
        resource = self.setup_helper.create_replica_storage()
        resource_info = self.setup_helper.run_icommand(["iadmin", "lr", resource.name])
        self.assertIn("resc_name: %s" % resource.name, resource_info)
        self.assertIn("resc_def_path: %s" % resource.location, resource_info)

    def tearDown(self):
        self.test_with_baton.tear_down()

    def _assert_metadata_in_retrieved(self, metadata: Metadata, retrieved_metadata: str):
        """
        Assert that the given metadata is in the metadata information retrieved via an `imeta` command.
        :param metadata: the metadata to expect
        :param retrieved_metadata: string representation of metadata, retrieved via an `imeta` command
        """
        for attribute in metadata:
            attribute_values = metadata[attribute]
            if not isinstance(attribute_values, list):
                attribute_values = [attribute_values]

            for value in attribute_values:
                self.assertIn("attribute: %s\nvalue: %s" % (attribute, value), retrieved_metadata)



if __name__ == "__main__":
    unittest.main()
