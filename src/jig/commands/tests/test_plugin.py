# coding=utf-8
from os.path import dirname, isdir, isfile, join
from os import makedirs
from tempfile import mkdtemp
from contextlib import nested

from mock import Mock, patch

from jig.tests.testcase import (CommandTestCase, PluginTestCase,
    cd_gitrepo, cwd_bounce)
from jig.tests.mocks import MockPlugin
from jig.exc import ForcedExit
from jig.plugins import (set_jigconfig, get_jigconfig, create_plugin,
    PluginManager)
from jig.plugins.testrunner import Expectation, SuccessResult
from jig.commands import plugin


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
        Adds a plugin to the jig initialized Git repository.
        """
        config = get_jigconfig(self.gitrepodir)
        pm = PluginManager(config)
        pm.add(plugin_dir)
        set_jigconfig(self.gitrepodir, pm.config)

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

        config = get_jigconfig(self.gitrepodir)

        # The config now contains our section
        self.assertTrue(config.has_section('plugin:a:a'))

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

        self.assertEqual(
            u'Added plugin a in bundle a to the repository.\n',
            self.output)

    def test_add_plugin_by_url(self):
        """
        Add a plugin from a Git URL.
        """
        def clone(plugin, to_dir):
            makedirs(to_dir)
            create_plugin(to_dir, template='python',
                bundle='a', name='a')

        with nested(
            patch('jig.commands.plugin.expanduser'),
            patch('jig.commands.plugin.clone')) as (e, c):
            # Instead of giving the user's home directory, let's force the
            # clone to occur in the test directory.
            e.return_value = self.plugindir
            c.side_effect = clone

            self.run_command('add --gitrepo {} http://repo'.format(
                self.gitrepodir))

        # A call was made to expanduser, this shows we were trying to do
        # something with the user's home directory.
        self.assertEqual('~', e.call_args[0][0])
        # And clone was called with our URL and would have performed the
        # operation in our test directory.
        self.assertEqual('http://repo', c.call_args[0][0])
        self.assertIn(self.plugindir, c.call_args[0][1])

    def test_add_plugin_by_url_jig_exists(self):
        """
        Add a plugin by URL if the ~/.jig directory already exists.
        """
        # Create the ~/.jig directory to make sure our command can handle this
        # condition.
        makedirs(join(self.plugindir, '.jig'))

        def clone(plugin, to_dir):
            makedirs(to_dir)
            create_plugin(to_dir, template='python',
                bundle='a', name='a')

        with nested(
            patch('jig.commands.plugin.expanduser'),
            patch('jig.commands.plugin.clone')) as (e, c):
            # Instead of giving the user's home directory, let's force the
            # clone to occur in the test directory.
            e.return_value = self.plugindir
            c.side_effect = clone

            self.run_command('add --gitrepo {} http://repo'.format(
                self.gitrepodir))

        # It should suffice to make sure that clone was called
        self.assertTrue(c.called)

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

        config = get_jigconfig(self.gitrepodir)

        # It should be removed from our config now
        self.assertFalse(config.has_section('plugin:bundle:name'))

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

        with patch('jig.commands.plugin.PluginTestRunner') as ptr:
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

        with patch('jig.commands.plugin.PluginTestRunner') as ptr:
            ptr.return_value = Mock()
            ptr.return_value.run = Mock(return_value=results)

            with cwd_bounce(plugin_dir):
                self.run_command('test')

        self.assertResults(u'''
            01 – 02 Pass

            Pass 1, Fail 0''', self.output)
