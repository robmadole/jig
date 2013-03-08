from stat import S_IXUSR
from os import rmdir, stat, makedirs
from os.path import isfile, join
from textwrap import dedent
from tempfile import mkdtemp
from calendar import timegm
from ConfigParser import ConfigParser
from datetime import datetime, timedelta

from git import Git
from mock import patch

from jig.tests.testcase import JigTestCase, PluginTestCase
from jig.exc import (NotGitRepo, AlreadyInitialized,
    GitRepoNotInitialized)
from jig.plugins import (initializer, get_jigconfig, set_jigconfig,
    PluginManager, create_plugin, available_templates)
from jig.plugins.tools import (
    update_plugins, last_checked_for_updates, set_checked_for_updates)


class TestPluginConfig(JigTestCase):

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
            get_jigconfig(self.gitrepodir)

    def test_get_config(self):
        """
        Get a config.
        """
        initializer(self.gitrepodir)

        plugins = get_jigconfig(self.gitrepodir)

        self.assertTrue(isinstance(plugins, ConfigParser))
        self.assertTrue(isfile(join(self.gitrepodir, '.jig', 'plugins.cfg')))

    def test_save_config_not_initialized(self):
        """
        Raises an error if saving a config where there is not Git repo.
        """
        with self.assertRaises(GitRepoNotInitialized):
            # It hasn't been initialized at this point, this should fail
            set_jigconfig(self.gitrepodir, config=None)

    def test_save_config(self):
        """
        Can save a config.
        """
        config = initializer(self.gitrepodir)

        config.add_section('test')
        config.set('test', 'foo', 'bar')

        set_jigconfig(self.gitrepodir, config=config)


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
        self.assertTrue(S_IXUSR & sinfo.st_mode)

        config = ConfigParser()
        config.read(join(plugin_dir, 'config.cfg'))

        self.assertEqual(set(('settings', 'plugin')), set(config.sections()))
        self.assertEqual('test', config.get('plugin', 'bundle'))
        self.assertEqual('plugin', config.get('plugin', 'name'))
        self.assertEqual([], config.items('settings'))

    def test_new_plugin_compat_plugin_manager(self):
        """
        New plugins are compatible with the :py:class:`PluginManager`
        """
        plugin_dir = create_plugin(self.plugindir, template='python',
            bundle='test', name='plugin')

        pm = PluginManager(self.jigconfig)

        pm.add(plugin_dir)

        self.assertEqual(1, len(pm.plugins))
        self.assertEqual('plugin', pm.plugins[0].name)


class TestUpdatePlugins(PluginTestCase):

    """
    Plugins can be updated if installed via URL.

    """
    def test_update_empty_result(self):
        """
        If no plugins are installed, results are empty
        """
        # None are installed so we get an empty list
        self.assertEqual({}, update_plugins(self.gitrepodir))

    def test_update_results(self):
        """
        If we have two plugins that are updated.
        """
        plugins_dir = join(self.gitrepodir, '.jig', 'plugins')
        fake_cloned_plugin = join(plugins_dir, 'abcdef1234567890')

        makedirs(fake_cloned_plugin)

        create_plugin(fake_cloned_plugin, bundle='a', name='a')
        create_plugin(fake_cloned_plugin, bundle='b', name='b')

        with patch.object(Git, 'execute'):
            # Fake the git pull command
            mock_execute = Git.execute

            Git.execute.return_value = (0, 'Already up to date.', '')

            results = update_plugins(self.gitrepodir)

        pm, value = results.items()[0]

        # We have our two plugins from the manager
        self.assertEquals(2, len(pm.plugins))

        # And it called ``git pull`` on the repository
        mock_execute.assert_called_once_with(
            ['git', 'pull'], with_extended_output=True)


class TestCheckedForUpdates(PluginTestCase):

    """
    Determining and setting the date plugins were last checked for updates.

    """
    def test_set_last_checked(self):
        """
        Can set the date last checked.
        """
        now = timegm(datetime.utcnow().replace(microsecond=0).timetuple())
        config = set_checked_for_updates(self.gitrepodir)

        actual = int(config.get('jig', 'last_checked_for_updates'))

        self.assertEqual(actual, now)

    def test_no_last_checked(self):
        """
        If the repo has never been checked for an update.
        """
        last_check = last_checked_for_updates(self.gitrepodir)

        self.assertEqual(0, last_check)

    def test_last_checked(self):
        """
        Can determine the last time checked.
        """
        now = datetime.utcnow().replace(microsecond=0)

        set_jigconfig(self.gitrepodir,
                      config=set_checked_for_updates(self.gitrepodir))

        date = last_checked_for_updates(self.gitrepodir)

        self.assertEqual(now, date)

    def test_set_last_checked_older_date(self):
        """
        Can set the date to an older value than now.
        """
        now = datetime.utcnow()
        older = now - timedelta(days=5)
        config = set_checked_for_updates(self.gitrepodir, date=older)

        now = timegm(now.timetuple())
        actual = int(config.get('jig', 'last_checked_for_updates'))
        expected = timegm(older.replace(microsecond=0).timetuple())

        self.assertEqual(actual, expected)
        self.assertGreater(now, actual)
