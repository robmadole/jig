# coding=utf-8
from os.path import dirname, isdir, isfile, join
from os import makedirs
from tempfile import mkdtemp
from contextlib import nested

from mock import Mock, patch

from jig.tests.testcase import (CommandTestCase, PluginTestCase,
    cd_gitrepo, cwd_bounce, result_with_hint)
from jig.tests.mocks import MockPlugin
from jig.tools import NumberedDirectoriesToGit
from jig.exc import ForcedExit
from jig.plugins import (set_jigconfig, get_jigconfig, create_plugin,
    PluginManager)
from jig.plugins.testrunner import (Expectation, SuccessResult,
    FailureResult, REPORTER_HORIZONTAL_DIVIDER)
from jig.gitutils import clone
from jig.commands import plugin
from jig.commands.hints import (
    FORK_PROJECT_GITHUB, NO_PLUGINS_INSTALLED, USE_RUNNOW, INVALID_RANGE)


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

        self.assertResults(
            result_with_hint(
                u'No plugins installed.',
                NO_PLUGINS_INSTALLED),
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

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(result_with_hint(u'''
            Installed plugins

            Plugin name               Bundle name
            plugin01................. test01
            plugin02................. test02
            plugin03................. test03
            ''', USE_RUNNOW), self.output)

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

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(result_with_hint(u'''
            Installed plugins

            Plugin name               Bundle name
            plugin01................. test
            plugin02................. test
            plugin03................. test
            ''', USE_RUNNOW), self.output)

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

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(result_with_hint(u'''
            Installed plugins

            Plugin name               Bundle name
            a........................ a
            b........................ b
            c........................ c
            ''', USE_RUNNOW), self.output)

    @cd_gitrepo
    def test_add_bad_plugin(self):
        """
        Only adds a plugin if it's valid.
        """
        # This is not a valid plugin directory, it's empty
        tmp_dir = mkdtemp()

        with self.assertRaises(ForcedExit):
            self.run_command('add {0}'.format(tmp_dir))

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
        self.run_command('add {0}'.format(plugin_dir))

        config = get_jigconfig(self.gitrepodir)

        # The config now contains our section
        self.assertTrue(config.has_section('plugin:a:a'))

        self.assertResults(
            u'''
            Added plugin a in bundle a to the repository.

            Run the plugins in the current repository with this command:

                $ jig runnow

            Jig works off of your staged files in the Git repository index.
            You place things in the index with `git add`. You will need to stage
            some files before you can run Jig.''',
            self.output)

    def test_add_plugin_to_git_repo(self):
        """
        Add a plugin when not inside the Git repository.
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='a', name='a')

        self.run_command('add --gitrepo {0} {1}'.format(
            self.gitrepodir, plugin_dir))

        self.assertResults(
            u'''
            Added plugin a in bundle a to the repository.

            Run the plugins in the current repository with this command:

                $ jig runnow

            Jig works off of your staged files in the Git repository index.
            You place things in the index with `git add`. You will need to stage
            some files before you can run Jig.''',
            self.output)

    def test_add_plugin_by_url(self):
        """
        Add a plugin from a Git URL.
        """
        def clone_fake(plugin, to_dir, branch=None):
            makedirs(to_dir)
            create_plugin(to_dir, template='python',
                bundle='a', name='a')

        with patch('jig.commands.plugin.clone') as c:
            c.side_effect = clone_fake

            self.run_command('add --gitrepo {0} http://repo'.format(
                self.gitrepodir))

        # And clone was called with our URL and would have performed the
        # operation in our test directory.
        self.assertEqual('http://repo', c.call_args[0][0])
        self.assertIn('{0}/.jig/plugins/'.format(self.gitrepodir),
            c.call_args[0][1])
        self.assertEqual(None, c.call_args[0][2])

    def test_add_plugin_by_url_with_branch(self):
        """
        Add a plugin from a Git URL, targeting a specific branch.
        """
        def clone_fake(plugin, to_dir, branch=None):
            makedirs(to_dir)
            create_plugin(to_dir, template='python',
                bundle='a', name='a')

        with patch('jig.commands.plugin.clone') as c:
            c.side_effect = clone_fake

            self.run_command('add --gitrepo {0} http://url.com/repo@alternate'.format(
                self.gitrepodir))

        # And the branch name was passed to clone
        self.assertEqual('alternate', c.call_args[0][2])

    def test_update_existing_plugins(self):
        """
        Can update an existing plugin.
        """
        # Make our remote repository so we have something to pull from
        origin_repo = mkdtemp()
        root_commit_dir = join(origin_repo, '01')
        makedirs(root_commit_dir)

        # Create a plugin in the repo
        create_plugin(root_commit_dir, template='python',
            bundle='a', name='a')
        create_plugin(root_commit_dir, template='python',
            bundle='b', name='b')

        # This is the directory we will clone
        ngd = NumberedDirectoriesToGit(origin_repo)
        dir_to_clone = ngd.repo.working_dir

        # This is a trick, we give it the dir_to_clone when asked to install it
        def clone_local(plugin, to_dir, branch):
            # Instead of jumping on the Internet to clone this, we will use the
            # local numbered directory repository we setup above. This will
            # allow our update to occur with a git pull and avoid network
            # traffic which is always faster for tests.
            clone(dir_to_clone, to_dir)

        # First thing is to install the the plugin
        with patch('jig.commands.plugin.clone') as c:
            c.side_effect = clone_local

            self.run_command('add --gitrepo {0} http://repo'.format(
                self.gitrepodir))

        self.run_command('update --gitrepo {0}'.format(
            self.gitrepodir))

        self.assertResults("""
            Updating plugins

            Plugin a, b in bundle a, b
                Already up-to-date.""",
            self.output)

    def test_update_existing_plugins_no_plugins(self):
        """
        If an attempt is made to update plugins when none are installed.
        """
        self.run_command('update --gitrepo {0}'.format(
            self.gitrepodir))

        self.assertResults("No plugins to update.", self.output)

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

        self.run_command('add -r {0} {1}'.format(self.gitrepodir, plugin_dir))

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

        self.run_command('add -r {0} {1}'.format(self.gitrepodir, plugin_dir))

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

        self.run_command('add -r {0} {1}'.format(self.gitrepodir, plugin_dir1))
        self.run_command('add -r {0} {1}'.format(self.gitrepodir, plugin_dir2))

        with self.assertRaises(ForcedExit):
            # Leave the bundle out, this should make our command error out
            self.run_command('remove -r {0} name'.format(self.gitrepodir))

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

        self.assertResults(
            result_with_hint(
                u'Language php is not supported yet.',
                FORK_PROJECT_GITHUB),
            self.error)

    def test_create_plugin_already_exists(self):
        """
        Cannot create a plugin if the destination already exists.
        """
        save_dir = dirname(create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name'))

        with self.assertRaises(ForcedExit):
            # We just created a plugin in this directory, so it should fail
            self.run_command('create --dir {0} name bundle'.format(save_dir))

        self.assertEqual(
            u'A plugin with this name already exists in this '
            u'directory: {0}.\n'.format(save_dir),
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
        self.run_command('create --dir {0} name bundle'.format(self.plugindir))

        self.assertTrue(isdir(join(self.plugindir, 'name')))

    def test_create_plugin_defaults_python(self):
        """
        Creates a plugin with the default language of python.
        """
        self.run_command(
            'create --dir {0} --language python name bundle'.format(
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
            self.run_command('test {0}'.format(plugin_dir))

        self.assertIn('Could not find any tests:', self.error)
        self.assertIn('{0}/tests'.format(plugin_dir), self.error)

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

            self.run_command('test {0}'.format(plugin_dir))

        self.assertResults(u'''
            01 – 02 Pass

            Pass 1, Fail 0''', self.output)

    def test_runs_specific_test(self):
        """
        Will run a specific test.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        with patch('jig.commands.plugin.PluginTestRunner') as ptr:
            ptr.return_value = Mock()
            ptr.return_value.run = Mock(return_value=[])

            self.run_command('test -r 4..5 {0}'.format(plugin_dir))

        ptr.return_value.run.assert_called_with(test_range=[(4, 5)])

    def test_handles_range_error(self):
        """
        If an improper range is given, provides a helpful error message.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        with self.assertRaises(ForcedExit):
            # Bad range "a.b"
            self.run_command('test -r a.b {0}'.format(plugin_dir))

        self.assertResults(
            result_with_hint(
                u'a.b is an invalid numbered test range',
                INVALID_RANGE),
            self.error)

    def test_plugin_test_failure(self):
        """
        Fails with exit code other than 0.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        expectation = Expectation((1, 2), None, u'bbb')
        results = [
            FailureResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin())]

        with patch('jig.commands.plugin.PluginTestRunner') as ptr:
            ptr.return_value = Mock()
            ptr.return_value.run = Mock(return_value=results)

            with self.assertRaises(ForcedExit):
                self.run_command('test {0}'.format(plugin_dir))

        self.assertResults(u'''
            01 – 02 Fail

            Actual
            {0}

            aaa

            Diff
            {0}

            - bbb
            + aaa

            Pass 0, Fail 1'''.format(REPORTER_HORIZONTAL_DIVIDER),
            self.error)

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

    def test_formats_results_verbose(self):
        """
        Will return test results with stdin and stdout.
        """
        plugin_dir = create_plugin(mkdtemp(), template='python',
            bundle='bundle', name='name')

        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin(), stdin='a\n', stdout='b\n')]

        with patch('jig.commands.plugin.PluginTestRunner') as ptr:
            ptr.return_value = Mock()
            ptr.return_value.run = Mock(return_value=results)

            self.run_command('test -v {0}'.format(plugin_dir))

        self.assertResults(u'''
            01 – 02 Pass

            stdin (sent to the plugin)

                a

            stdout (received from the plugin)

                b

            {0}
            Pass 1, Fail 0'''.format(REPORTER_HORIZONTAL_DIVIDER),
            self.output)
