# coding=utf-8
import sys
from contextlib import nested
from tempfile import mkstemp

from mock import Mock, patch

from jig.exc import PluginError
from jig.entrypoints import main
from jig.tests.testcase import JigTestCase, ViewTestCase, CommandTestCase
from jig.formatters import tap, fancy
from jig.commands.base import (
    get_formatter, list_commands, create_view, add_plugin, BaseCommand)

try:
    import argparse
except ImportError:   # pragma: no cover
    from backports import argparse


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


class TestGetFormatter(JigTestCase):

    """
    Get a formatter used to format Jig results.

    """
    def test_default(self):
        """
        Get the default formatter.
        """
        self.assertEqual(
            fancy.FancyFormatter,
            get_formatter('notcorrect')
        )

    def test_tap(self):
        """
        Get the tap formatter.
        """
        self.assertEqual(
            tap.TapFormatter,
            get_formatter('tap')
        )

    def test_fancy(self):
        """
        Get the fancy formatter.
        """
        self.assertEqual(
            fancy.FancyFormatter,
            get_formatter('fancy')
        )


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


class TestBaseCommandCrashReport(CommandTestCase):

    """
    Base command catches uncaught exceptions and creates a crash report.

    """
    def setUp(self):
        self.mock_parser = argparse.ArgumentParser(
            description='Mock parser')

        self.uncaught_exception = Exception()
        self.fd, self.report_file = mkstemp()

    def run_command(self, command=None):
        class MockCommand(BaseCommand):
            parser = self.mock_parser

            def process(self, args):
                raise self.uncaught_exception

        self.command = MockCommand
        self.command.uncaught_exception = self.uncaught_exception

        with nested(
            patch('jig.commands.base.sys'),
            patch('jig.commands.base.mkstemp')
        ) as (mock_sys, mock_mkstemp):
            mock_sys.exc_info.side_effect = sys.exc_info
            mock_mkstemp.return_value = (1, self.report_file)

            super(TestBaseCommandCrashReport, self).run_command(command)

        with open(self.report_file) as fh:
            report_contents = fh.read()

        message = mock_sys.stderr.write.call_args[0][0]
        exit_code = mock_sys.exit.call_args[0][0]

        return report_contents, message, exit_code

    def test_exits_with_2(self):
        """
        A crash report exits with 2 instead of 1.
        """
        self.mock_parser.add_argument('a')

        report_contents, message, exit_code = self.run_command('1')

        self.assertEqual(2, exit_code)

    def test_includes_arguments(self):
        """
        The arguments for the command are included in the report.
        """
        self.mock_parser.add_argument('a')
        self.mock_parser.add_argument('-b')
        self.mock_parser.add_argument('--c')

        report_contents, message, exit_code = self.run_command('1 -b 2 --c=3')

        self.assertIn(
            "Namespace(a='1', b='2', c='3')",
            report_contents
        )

    def test_includes_formatted_traceback(self):
        """
        A formatted traceback is included.
        """
        self.mock_parser.add_argument('a')

        report_contents, message, exit_code = self.run_command('1')

        self.assertIn(
            'Traceback (most recent call last)',
            report_contents
        )

    def test_mentions_uncaught_exception(self):
        """
        The specific exception is included in the traceback.
        """
        self.uncaught_exception = Exception('Uncaught')

        self.mock_parser.add_argument('a')

        report_contents, message, exit_code = self.run_command('1')

        self.assertIn(
            'Exception: Uncaught',
            report_contents
        )

    def test_displays_information_about_crash_report(self):
        """
        Written to stderr is human-readable information about what happened.
        """
        self.mock_parser.add_argument('a')

        report_contents, message, exit_code = self.run_command('1')

        self.assertIn(
            'CRASH REPORT',
            message
        )

    def test_mentions_the_crash_report_file(self):
        """
        Tells the user where the crash report is.
        """
        self.mock_parser.add_argument('a')

        report_contents, message, exit_code = self.run_command('1')

        self.assertIn(
            self.report_file,
            message
        )


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
            '{0}/.jig/plugins/{1}'.format(self.gitrepodir, MockUUID.hex),
            None)

        # The plugin manager was given the newly cloned location
        self.pm.add.assert_called_with(
            '{0}/.jig/plugins/{1}'.format(self.gitrepodir, MockUUID.hex))

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
            '{0}/.jig/plugins/{1}'.format(self.gitrepodir, MockUUID.hex),
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
            '{0}/.jig/plugins/{1}'.format(self.gitrepodir, MockUUID.hex))
