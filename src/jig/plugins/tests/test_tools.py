from os import rmdir, stat
from os.path import isfile, join
from textwrap import dedent
from tempfile import mkdtemp
from ConfigParser import ConfigParser

from jig.tests.testcase import jigTestCase, PluginTestCase
from jig.exc import (NotGitRepo, AlreadyInitialized,
    GitRepoNotInitialized)
from jig.plugins import (initializer, get_bcconfig, set_bcconfig,
    PluginManager, create_plugin, available_templates)


class TestPluginConfig(jigTestCase):

    """
    Test plugin config file handling.

    """
    def test_not_git_repo(self):
        """
        Refuses to initialize a non-Git repo.
        """
        badrepo = mkdtemp()

        with self.assertRaises(NotGitRepo):
            initializer(badrepo)

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

        with self.assertRaises(AlreadyInitialized):
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
        with self.assertRaises(GitRepoNotInitialized):
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


class TestCreatePlugin(PluginTestCase):

    """
    Test the plugin creation utility.

    """
    def setUp(self):
        super(TestCreatePlugin, self).setUp()

        self.plugindir = mkdtemp()

    def test_list_available_templates(self):
        """
        List available templates for creating plugins.
        """
        self.assertEqual(['python'], available_templates())

    def test_missing_directory(self):
        """
        Will not try to create a plugin in a missing directory.
        """
        # Remove this so the create_plugin function has nowhere to go.
        rmdir(self.plugindir)

        with self.assertRaises(ValueError):
            create_plugin(self.plugindir, template='python',
                bundle='test', name='plugin')

    def test_creates_plugin(self):
        """
        Can create a plugin.
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='test', name='plugin')

        pre_commit_file = join(plugin_dir, 'pre-commit')

        # We have a pre-commit file
        self.assertTrue(isfile(pre_commit_file))

        # And it's executable
        sinfo = stat(pre_commit_file)
        self.assertEqual(33261, sinfo.st_mode)

        self.assertEqual(dedent("""
            [plugin]
            bundle = test
            name = plugin

            [settings]
            """).strip(),
            open(join(plugin_dir, 'config.cfg')).read().strip())

    def test_new_plugin_compat_plugin_manager(self):
        """
        New plugins are compatible with the :py:class:`PluginManager`
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='test', name='plugin')

        pm = PluginManager(self.bcconfig)

        pm.add(plugin_dir)

        self.assertEqual(1, len(pm.plugins))
        self.assertEqual('plugin', pm.plugins[0].name)
