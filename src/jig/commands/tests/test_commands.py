# coding=utf-8
import sys

from mock import Mock, patch

from jig.exc import PluginError
from jig.entrypoints import main
from jig.tests.testcase import JigTestCase, ViewTestCase, CommandTestCase
from jig.commands.base import (
    list_commands, create_view, add_plugin, BaseCommand)


class TestCommands(ViewTestCase):

    """
    Test the main parts of the command-line utility.

    """

    help_output_marker = '''
        usage: jig [-h] COMMAND

        optional arguments:
          -h, --help  show this help message and exit'''

    def setUp(self):
        self.view = create_view()

        self.view.collect_output = True
        self.view.exit_on_exception = False

    def test_main(self):
        """
        Will output help if no arguments are given
        """
        with patch.object(sys, 'stdout') as p:
            main()

        output = ''
        for stdout_call in p.write.call_args_list:
            output += stdout_call[0][0]

        self.assertResultsIn(self.help_output_marker, output)

    def test_main_help(self):
        """
        Will provide help menu when ran with no arguments.
        """
        commands = list_commands()

        self.view.print_help(commands)

        self.assertResultsIn(self.help_output_marker, self.output)


class TestBaseCommand(CommandTestCase):

    """
    Test our base command class.

    """
    def test_abstract_process(self):
        """
        The process method is abstract.
        """
        class MissingProcessCommand(BaseCommand):
            parser = Mock()

        with self.assertRaises(NotImplementedError):
            MissingProcessCommand([])


class MockUUID(object):
    hex = 'abcdef1234567890'


class TestAddPlugin(JigTestCase):

    """
    Add a plugin from url or local file system.

    """
    def setUp(self):
        super(TestAddPlugin, self).setUp()

        self.pm = Mock()

        self.clone_patch = patch('jig.commands.base.clone')
        self.clone = self.clone_patch.start()

        self.rmtree_patch = patch('jig.commands.base.rmtree')
        self.rmtree = self.rmtree_patch.start()

        self.uuid_patch = patch('jig.commands.base.uuid')
        self.uuid = self.uuid_patch.start()
        self.uuid.return_value = MockUUID

    def tearDown(self):
        super(TestAddPlugin, self).tearDown()

        self.clone_patch.stop()
        self.rmtree_patch.stop()
        self.uuid_patch.stop()

    def test_add_file_system(self):
        """
        Adds a file system plugin.
        """
        add_plugin(self.pm, '/a/b/c', self.gitrepodir)

        # Since this was from the file system clone was not called
        self.assertFalse(self.clone.called)

        # The plugin manager add() method was called with the location verbatim
        self.pm.add.assert_called_with('/a/b/c')

    def test_add_file_system_error_skips_cleanup(self):
        """
        Cleanup only occurs if the plugin is URL-based
        """
        self.pm.add.side_effect = PluginError

        # Make sure that the error does bubble out
        with self.assertRaises(PluginError):
            add_plugin(self.pm, '/a/b/c', self.gitrepodir)

        # Since we didn't clone a repository, we should not clean anything up
        self.assertFalse(self.rmtree.called)

    def test_url_without_branch(self):
        """
        URL without a branch specifier.
        """
        add_plugin(self.pm, 'http://a.b/c', self.gitrepodir)

        # Since this was a URL clone was called with the full URL
        self.clone.assert_called_with(
            'http://a.b/c',
            '{}/.jig/plugins/{}'.format(self.gitrepodir, MockUUID.hex),
            None)

        # The plugin manager was given the newly cloned location
        self.pm.add.assert_called_with(
            '{}/.jig/plugins/{}'.format(self.gitrepodir, MockUUID.hex))

        # Since things went well, the cleanup function was not ran
        self.assertFalse(self.rmtree.called)

    def test_url_with_branch(self):
        """
        URL with a branch specifier.
        """
        add_plugin(self.pm, 'http://a.b/c@branch', self.gitrepodir)

        # Since this was a URL clone was called with the full URL
        self.clone.assert_called_with(
            'http://a.b/c',
            '{}/.jig/plugins/{}'.format(self.gitrepodir, MockUUID.hex),
            'branch')

    def test_cleanup_on_error_with_url(self):
        """
        Cleanup occurs on a plugin error.
        """
        self.pm.add.side_effect = PluginError

        # Make sure that the error does bubble out
        with self.assertRaises(PluginError):
            add_plugin(self.pm, 'http://a.b/c', self.gitrepodir)

        self.rmtree.assert_called_with(
            '{}/.jig/plugins/{}'.format(self.gitrepodir, MockUUID.hex))
