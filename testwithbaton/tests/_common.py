from abc import abstractmethod

from inflection import camelize

from testwithbaton.api import BatonImageVersion
from testwithbaton.models import BatonImage


class BatonImageContainer():
    """
    Container of a baton image.
    """
    @property
    @abstractmethod
    def baton_image(self) -> BatonImage:
        """
        A Docker baton image.
        :return: baton image
        """


def create_tests_for_all_baton_versions(test_superclass: type):
    """
    Create tests for all baton versions that inherit from the given test superclass.
    :param test_superclass: test superclass which must inherit from `BatonImageContainer`
    """
    for version in BatonImageVersion:
        class_name = "%sWithBaton%s" % (test_superclass.__name__, camelize(version.name[1:].lower()))

        @property
        def baton_image(self):
            return self._baton_image

        globals()[class_name] = type(
            class_name,
            (test_superclass, ),
            {
                "_baton_image": version.value,
                "baton_image": baton_image
            }
        )
