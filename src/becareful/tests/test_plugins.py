from os import rmdir
from os.path import isfile, join
from tempfile import mkdtemp
from ConfigParser import ConfigParser

from nose.plugins.attrib import attr

from becareful.tests.testcase import BeCarefulTestCase
from becareful.exc import NotGitRepo, AlreadyInitialized, GitRepoNotInitialized
from becareful.plugins import initializer, get_bcconfig, set_bcconfig, PluginManager


class TestPluginConfig(BeCarefulTestCase):

    """
    Test plugin config file handling.

    """
    @property
    def plugins(self):
        return get_bcconfig(self.gitrepodir)

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

    def test_save_config(self):
        """
        Can save a config.
        """
        config = initializer(self.gitrepodir)

        config.add_section('test')
        config.set('test', 'foo', 'bar')

        set_bcconfig(self.gitrepodir)


class TestPluginManager(BeCarefulTestCase):

    """
    Test the plugin manager.

    """
    def setUp(self):
        super(TestPluginManager, self).setUp()

        initializer(self.gitrepodir)

        self.bcconfig = get_bcconfig(self.gitrepodir)

    def test_has_empty_plugin_list(self):
        pm = PluginManager(self.bcconfig)

        self.assertEqual([], pm.plugins)

    def test_can_add_plugin(self):
        pm = PluginManager(self.bcconfig)

        pm.add(join(self.fixturesdir, 'plugin01'))
