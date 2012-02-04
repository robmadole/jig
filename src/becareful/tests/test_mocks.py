from mock import Mock

from becareful.tests.testcase import BeCarefulTestCase
from becareful.tests.mocks import MockPlugin


class TestMockPlugin(BeCarefulTestCase):

    """
    Mock plugin behaves correctly.

    """
    def test_create_unnamed_mock_plugin(self):
        """
        Create an unnamed mock plugin.
        """
        mp = MockPlugin()

        self.assertEqual('Unnamed', mp.name)

    def test_create_named_plugin(self):
        """
        Create a mock plugin with a specific name.
        """
        mp = MockPlugin(name='Specific')

        self.assertEqual('Specific', mp.name)

    def test_change_name_later(self):
        """
        Change a plugins name after it has been created.
        """
        mp = MockPlugin()

        mp.name = 'Specific'

        self.assertEqual('Specific', mp.name)

    def test_children_are_normal_mocks(self):
        """
        Calling an attribute returns a normal :py:class:`Mock`.
        """
        mp = MockPlugin()

        mock = mp.testattr

        self.assertTrue(isinstance(mock, Mock))
        self.assertFalse(isinstance(mock, MockPlugin))
