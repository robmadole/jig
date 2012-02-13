# coding=utf-8
import sys
from os.path import dirname, isdir, isfile, join
from tempfile import mkdtemp
from contextlib import nested

from mock import Mock, patch
from nose.plugins.attrib import attr

from becareful.entrypoints import main
from becareful.tests.testcase import (ViewTestCase, CommandTestCase,
    PluginTestCase, cd_gitrepo, cwd_bounce)
from becareful.tests.mocks import MockPlugin
from becareful.exc import ForcedExit
from becareful.plugins import (set_bcconfig, get_bcconfig, create_plugin,
    PluginManager)
from becareful.plugins.testrunner import Expectation, SuccessResult
from becareful.commands import init, runnow, plugin
from becareful.commands.base import list_commands, create_view, BaseCommand


class TestCommands(ViewTestCase):

    """
    Test the main parts of the command-line utility.

    """

    help_output = '''
        usage: becareful [-h] COMMAND

        optional arguments:
          -h, --help  show this help message and exit

        BeCareful commands:
          init        Initialize a Git repository for use with BeCareful
          plugin      Manage BeCareful plugins
          runnow      Run all plugins and show the results

        See `becareful COMMAND --help` for more information'''

    def setUp(self):
        self.view = create_view()

        self.view.collect_output = True
        self.view.exit_on_exception = False

    def test_main(self):
        with patch.object(sys, 'stdout') as p:
            main()

        output = ''
        for stdout_call in p.write.call_args_list:
            output += stdout_call[0][0]

        self.assertResults(self.help_output, output)

    def test_main_help(self):
        """
        Will provide help menu when ran with no arguments.
        """
        commands = list_commands()

        self.view.print_help(commands)

        self.assertResults(self.help_output, self.output)


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


class TestInitCommand(CommandTestCase):

    """
    Test the init subcommand.

    """
    command = init.Command

    def test_initialize_repo(self):
        """
        We inititialize a repository with BeCareful.
        """
        self.run_command(self.gitrepodir)

        self.assertEqual(
            u'Git repository has been initialized for use with BeCareful.\n',
            self.output)

    @cd_gitrepo
    def test_initialize_current_directory(self):
        """
        Defaults to the current directory and initializes.
        """
        # Leave the directory argument off, which should make the command
        # use the current working directory.
        self.run_command()

        self.assertEqual(
            u'Git repository has been initialized for use with BeCareful.\n',
            self.output)

    def test_handles_error(self):
        """
        Catches repository that do not exist.
        """
        with self.assertRaises(ForcedExit):
            self.run_command(mkdtemp())

        self.assertIn('is not a Git repository', self.error)


class TestRunNowCommand(CommandTestCase, PluginTestCase):

    """
    Test the runnow command.

    """
    command = runnow.Command

    def test_no_changes(self):
        """
        No changes have been made to the Git repository.
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        # Create the first commit
        self.commit(self.gitrepodir, 'a.txt', 'a')

        self.run_command(self.gitrepodir)

        self.assertEqual(u'No staged changes in the repository, '
            'skipping BeCareful.\n', self.output)

    def test_changes(self):
        """
        Changes are made and the plugin runs and gives us output.
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('becareful.runner.raw_input', create=True),
            patch('becareful.runner.sys')
        ) as (ri, r_sys):
            # Fake the raw_input call to return 'c'
            ri.return_value = 'c'

            self.run_command(self.gitrepodir)

        # Since we chose to cancel the commit by providing 'c', this should
        # exit with 1 which will indicate to Git that it needs to abort the
        # commit.
        r_sys.exit.assert_called_once_with(1)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: b.txt
                b is +

            Ran 1 plugin
                Info 0 Warn 1 Stop 0
            """, self.output)

    def test_handles_error(self):
        """
        An un-initialized BeCareful Git repository provides an error message.
        """
        with self.assertRaises(ForcedExit):
            self.run_command(mkdtemp())

        self.assertIn(u'This repository has not been initialized. Run '
            'becareful init GITREPO to set it up.\n', self.error)


class TestPluginCommand(CommandTestCase, PluginTestCase):

    """
    Test the plugin command.

    """
    command = plugin.Command

    def setUp(self):
        super(TestPluginCommand, self).setUp()

        self.plugindir = mkdtemp()

    def _add_plugin(self, plugin_dir):
        """
        Adds a plugin to the BeCareful initialized Git repository.
        """
        config = get_bcconfig(self.gitrepodir)
        pm = PluginManager(config)
        pm.add(plugin_dir)
        set_bcconfig(self.gitrepodir, pm.config)

    @cd_gitrepo
    def test_list_no_plugins(self):
        """
        No plugins are installed and the list is empty.
        """
        # Without the path argument, this should default to the current working
        # directory.
        self.run_command('list')

        self.assertEqual(
            u'No plugins installed.\n',
            self.output)

    def test_list_plugins_different_bundle(self):
        """
        Lists plugins correctly if they are in different bundles.
        """
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='test01', name='plugin01'))
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='test02', name='plugin02'))
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='test03', name='plugin03'))

        self.run_command('list -r {}'.format(self.gitrepodir))

        self.assertResults(u'''
            Installed plugins

            Plugin name               Bundle name
            plugin01................. test01
            plugin02................. test02
            plugin03................. test03
            ''', self.output)

    def test_list_plugins_same_bundle(self):
        """
        Lists plugins correctly if they are in the same bundle.
        """
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='test', name='plugin01'))
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='test', name='plugin02'))
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='test', name='plugin03'))

        self.run_command('list -r {}'.format(self.gitrepodir))

        self.assertResults(u'''
            Installed plugins

            Plugin name               Bundle name
            plugin01................. test
            plugin02................. test
            plugin03................. test
            ''', self.output)

    def test_lists_alphabetically(self):
        """
        Will list bundles and plugin names alphabetically.
        """
        # Add these in reverse order of alphabetical
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='c', name='c'))
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='b', name='b'))
        self._add_plugin(create_plugin(self.plugindir, template='python',
            bundle='a', name='a'))

        self.run_command('list -r {}'.format(self.gitrepodir))

        self.assertResults('''
            Installed plugins

            Plugin name               Bundle name
            a........................ a
            b........................ b
            c........................ c
            ''', self.output)

    @cd_gitrepo
    def test_add_bad_plugin(self):
        """
        Only adds a plugin if it's valid.
        """
        # This is not a valid plugin directory, it's empty
        tmp_dir = mkdtemp()

        with self.assertRaises(ForcedExit):
            self.run_command('add {}'.format(tmp_dir))

        self.assertRegexpMatches(self.error,
            u'The plugin file (.+)config.cfg is missing')

    @cd_gitrepo
    def test_add_plugin(self):
        """
        Adds a valid plugin.
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='a', name='a')

        # We are going to test whether it defaults --gitrepo to cwd
        self.run_command('add {}'.format(plugin_dir))

        self.assertEqual(
            u'Added plugin a in bundle a to the repository.\n',
            self.output)

    def test_add_plugin_to_git_repo(self):
        """
        Add a plugin when not inside the Git repository.
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='a', name='a')

        self.run_command('add --gitrepo {} {}'.format(
            self.gitrepodir, plugin_dir))

    @cd_gitrepo
    def test_remove_bad_plugin(self):
        """
        Only removes a plugin that has been installed.
        """
        with self.assertRaises(ForcedExit):
            self.run_command('remove a')

        self.assertEqual(
            u'This plugin does not exist.\n',
            self.error)

    @cd_gitrepo
    def test_remove_plugin(self):
        """
        Removes an installed plugin.
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='bundle', name='name')

        self.run_command('add -r {} {}'.format(self.gitrepodir, plugin_dir))

        # Remove with the --gitrepo defaulting to cwd again
        self.run_command('remove name bundle')

        self.assertEqual(
            u'Removed plugin name\n',
            self.output)

    @cd_gitrepo
    def test_remove_plugin_guesses_bundle(self):
        """
        Removes an installed plugin.
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='bundle', name='name')

        self.run_command('add -r {} {}'.format(self.gitrepodir, plugin_dir))

        # Leave the bundle name off so it can be guessed.
        self.run_command('remove name')

        self.assertEqual(
            u'Removed plugin name\n',
            self.output)

    def test_remove_plugin_same_name(self):
        """
        Exits because more than one plugin has the same name.

        If the bundle is not specified and more than one plugin has the same
        name, we can't assume which plugin they wish to remove. Error out and
        suggest they use the list command.
        """
        plugin_dir1 = create_plugin(mkdtemp(), template='python',
            bundle='bundle1', name='name')
        plugin_dir2 = create_plugin(mkdtemp(), template='python',
            bundle='bundle2', name='name')

        self.run_command('add -r {} {}'.format(self.gitrepodir, plugin_dir1))
        self.run_command('add -r {} {}'.format(self.gitrepodir, plugin_dir2))

        with self.assertRaises(ForcedExit):
            # Leave the bundle out, this should make our command error out
            self.run_command('remove -r {} name'.format(self.gitrepodir))

        self.assertEqual(
            u'More than one plugin has the name of name. Use the list '
            u'command to see installed plugins.\n',
            self.error)

    def test_create_with_bad_language(self):
        """
        Cannot create a plugin if the language is unavailable
        """
        with self.assertRaises(ForcedExit):
            # We just created a plugin in this directory, so it should fail
            self.run_command('create -l php name bundle')

        self.assertEqual(
            u'Language php is not supported yet, you can for this '
            u'project and add it though!\n',
            self.error)

    def test_create_plugin_already_exists(self):
        """
        Cannot create a plugin if the destination already exists.
        """
        save_dir = dirname(create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name'))

        with self.assertRaises(ForcedExit):
            # We just created a plugin in this directory, so it should fail
            self.run_command('create --dir {} name bundle'.format(save_dir))

        self.assertEqual(
            u'A plugin with this name already exists in this '
            u'directory: {}.\n'.format(save_dir),
            self.error)

    def test_create_plugin(self):
        """
        Can create a plugin.
        """
        with cwd_bounce(self.plugindir):
            self.run_command('create name bundle')

        self.assertTrue(isdir(join(self.plugindir, 'name')))
        self.assertTrue(isfile(join(self.plugindir, 'name', 'config.cfg')))

    def test_create_plugin_in_directory(self):
        """
        Creates a plugin in a given directory.
        """
        self.run_command('create --dir {} name bundle'.format(self.plugindir))

        self.assertTrue(isdir(join(self.plugindir, 'name')))

    def test_create_plugin_defaults_python(self):
        """
        Creates a plugin with the default language of python.
        """
        self.run_command(
            'create --dir {} --language python name bundle'.format(
                self.plugindir))

        with open(join(self.plugindir, 'name', 'pre-commit')) as fh:
            pre_commit = fh.readlines()

        self.assertEqual('#!/usr/bin/env python\n', pre_commit[0])

    def test_plugin_tests_none_found(self):
        """
        Run tests for a plugin where no tests are found.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        with self.assertRaises(ForcedExit):
            self.run_command('test {}'.format(plugin_dir))

        self.assertIn('Could not find any tests:', self.error)
        self.assertIn('{}/tests'.format(plugin_dir), self.error)

    def test_formats_results(self):
        """
        Will return test results.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin())]

        with patch('becareful.commands.plugin.PluginTestRunner') as ptr:
            ptr.return_value = Mock()
            ptr.return_value.run = Mock(return_value=results)

            self.run_command('test {}'.format(plugin_dir))

        self.assertResults(u'''
            01 – 02 Pass

            Pass 1, Fail 0''', self.output)

    def test_plugin_defaults_to_cwd(self):
        """
        Running the plugins tests defaults to the current working directory.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin())]

        with patch('becareful.commands.plugin.PluginTestRunner') as ptr:
            ptr.return_value = Mock()
            ptr.return_value.run = Mock(return_value=results)

            with cwd_bounce(plugin_dir):
                self.run_command('test')

        self.assertResults(u'''
            01 – 02 Pass

            Pass 1, Fail 0''', self.output)
