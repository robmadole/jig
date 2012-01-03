# coding=utf-8
from tempfile import mkdtemp

from nose.plugins.attrib import attr

from becareful.tests.testcase import (CommandTestCase, PluginTestCase,
    cd_gitrepo)
from becareful.exc import ForcedExit
from becareful.plugins import (set_bcconfig, get_bcconfig, create_plugin,
    PluginManager)
from becareful.commands import init, runnow, plugin


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
            u'Git repository has been initialized for use with BeCareful\n',
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
            u'Git repository has been initialized for use with BeCareful\n',
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
            'skipping BeCareful\n', self.output)

    def test_changes(self):
        """
        Changes are made and the plugin runs and gives us output.
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        self.run_command(self.gitrepodir)

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
            'becareful init GITREPO to set it up\n', self.error)


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

    @attr('focus')
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
