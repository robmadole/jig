import json
from os import rmdir
from os.path import isfile, join, dirname
from tempfile import mkdtemp
from ConfigParser import ConfigParser

from becareful.tests.testcase import BeCarefulTestCase, PluginTestCase
from becareful.tests.utils import diffindexfrom
from becareful.diffconvert import GitDiffIndex
from becareful.exc import (NotGitRepo, AlreadyInitialized,
    GitRepoNotInitialized, PluginError)
from becareful.plugins import (initializer, get_bcconfig, set_bcconfig,
    PluginManager)


class TestPluginConfig(BeCarefulTestCase):

    """
    Test plugin config file handling.

    """
    def test_not_git_repo(self):
        """
        Refuses to initialize a non-Git repo.
        """
        badrepo = mkdtemp()

        try:
            with self.assertRaises(NotGitRepo) as c:
                initializer(badrepo)
        finally:
            rmdir(badrepo)

    def test_can_initialize(self):
        """
        Can initialize the Git repo.
        """
        # Should return a ConfigParser instance
        plugins = initializer(self.gitrepodir)

        self.assertTrue(isinstance(plugins, ConfigParser))

    def test_already_initialized(self):
        """
        Catches an attempt to initialize a directory that already has been.
        """
        # Initialize it once
        initializer(self.gitrepodir)

        with self.assertRaises(AlreadyInitialized) as c:
            # Initialize the same directory again
            initializer(self.gitrepodir)

    def test_get_config_not_initialized(self):
        """
        Attempting to get a config for a directory not initialized.
        """
        with self.assertRaises(GitRepoNotInitialized):
            get_bcconfig(self.gitrepodir)

    def test_get_config(self):
        """
        Get a config.
        """
        initializer(self.gitrepodir)

        plugins = get_bcconfig(self.gitrepodir)

        self.assertTrue(isinstance(plugins, ConfigParser))
        self.assertTrue(isfile(join(self.gitrepodir, '.bc', 'plugins.cfg')))

    def test_save_config_not_initialized(self):
        """
        Raises an error if saving a config where there is not Git repo.
        """
        with self.assertRaises(GitRepoNotInitialized) as c:
            # It hasn't been initialized at this point, this should fail
            set_bcconfig(self.gitrepodir, config=None)

    def test_save_config(self):
        """
        Can save a config.
        """
        config = initializer(self.gitrepodir)

        config.add_section('test')
        config.set('test', 'foo', 'bar')

        set_bcconfig(self.gitrepodir, config=config)


class TestPluginManager(PluginTestCase):

    """
    Test the plugin manager.

    """
    def test_has_empty_plugin_list(self):
        """
        A freshly initialized repo has no plugins.
        """
        pm = PluginManager(self.bcconfig)

        self.assertEqual([], pm.plugins)

    def test_has_one_plugin(self):
        """
        We can add one plugin to the main config file.
        """
        self._add_plugin(self.bcconfig, 'plugin01')

        pm = PluginManager(self.bcconfig)

        self.assertEqual(1, len(pm.plugins))

        plugin = pm.plugins[0]

        self.assertEqual('test01', plugin.bundle)
        self.assertEqual('plugin01', plugin.name)

    def test_ignores_non_plugin_sections(self):
        """
        Other sections of the config do not get seen as a plugin.
        """
        self._add_plugin(self.bcconfig, 'plugin01')

        self.bcconfig.add_section('nonplugin')
        self.bcconfig.set('nonplugin', 'def1', '1')

        pm = PluginManager(self.bcconfig)

        self.assertEqual(1, len(pm.plugins))

    def test_can_add_plugin(self):
        """
        Test the add method on the plugin manager.
        """
        # Config is empty
        pm = PluginManager(self.bcconfig)

        pm.add(join(self.fixturesdir, 'plugin01'))

        self.assertEqual(1, len(pm.plugins))

    def test_detects_bad_plugin_config(self):
        """
        Tests a bad plugin config from the main config.
        """
        self._add_plugin(self.bcconfig, 'plugin02')

        with self.assertRaises(PluginError) as ec:
            pm = PluginManager(self.bcconfig)

        self.assertIn('Could not parse config file', str(ec.exception))

    def test_add_bad_plugin_config(self):
        """
        Adding a bad plugin catches parsing errors.
        """
        pm = PluginManager(self.bcconfig)

        with self.assertRaises(PluginError) as ec:
            pm.add(join(self.fixturesdir, 'plugin02'))

        self.assertIn('File contains parsing errors', str(ec.exception))

    def test_add_plugin_no_config_file(self):
        """
        Will handle a plugin that has no config file.
        """
        pm = PluginManager(self.bcconfig)

        with self.assertRaises(PluginError) as ec:
            pm.add(join(self.fixturesdir, 'plugin03'))

        self.assertIn('The plugin file', str(ec.exception))
        self.assertIn('is missing', str(ec.exception))

    def test_add_plugin_no_plugin_section(self):
        """
        Will not add a plugin with missing plugin section.
        """
        pm = PluginManager(self.bcconfig)

        with self.assertRaises(PluginError) as ec:
            pm.add(join(self.fixturesdir, 'plugin04'))

        self.assertEqual(
            'The plugin config does not contain a [plugin] section',
            str(ec.exception))

    def test_add_plugin_no_settings_section(self):
        """
        Adds a plugin if it has no settings.
        """
        pm = PluginManager(self.bcconfig)

        pm.add(join(self.fixturesdir, 'plugin05'))

        self.assertEqual(1, len(pm.plugins))

    def test_missing_bundle_and_name(self):
        """
        Will not add a plugin if it is missing a bundle or name.
        """
        pm = PluginManager(self.bcconfig)

        with self.assertRaises(PluginError) as ec:
            pm.add(join(self.fixturesdir, 'plugin06'))

        self.assertIn('Could not find the bundle or name', str(ec.exception))

    def test_cannot_add_plugin_twice(self):
        """
        After a plugin has been added, it can't be added again.
        """
        pm = PluginManager(self.bcconfig)

        with self.assertRaises(PluginError) as ec:
            pm.add(join(self.fixturesdir, 'plugin01'))
            # And the second time
            pm.add(join(self.fixturesdir, 'plugin01'))

        self.assertEqual('The plugin is already installed.',
            str(ec.exception))


class TestPlugin(PluginTestCase):

    """
    Test the individual plugins.

    """
    def setUp(self):
        super(TestPlugin, self).setUp()

        self.testrepodir = join(dirname(__file__), 'fixtures', 'repo01')

    def _git_diff_index(self, fixture):
        diffindex = diffindexfrom(fixture)

        return GitDiffIndex(self.testrepodir, diffindex)

    def test_new_file_pre_commit(self):
        """
        Test a new file pre-commit.
        """
        pm = PluginManager(self.bcconfig)

        pm.add(join(self.fixturesdir, 'plugin01'))
        gdi = self._git_diff_index('new_file')

        retcode, stdout, stderr = pm.plugins[0].pre_commit(gdi)

        data = json.loads(stdout)

        # Everything should have gone splendidly
        self.assertEqual(0, retcode)
        # Should contain our file that was added
        self.assertIn('argument.txt', data)
        # And our first line should be a warning
        self.assertEqual(
            [1, u'warn', u'The cast: is horrible'],
            data['argument.txt'][0])
