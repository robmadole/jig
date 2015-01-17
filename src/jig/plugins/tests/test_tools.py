from stat import S_IXUSR
from os import rmdir, stat, makedirs
from os.path import isfile, join
from tempfile import mkdtemp
from calendar import timegm
from ConfigParser import ConfigParser
from datetime import datetime, timedelta

from mock import patch

from jig.packages.sh import sh
from jig.tests.testcase import JigTestCase, PluginTestCase, cd_gitrepo
from jig.exc import (
    NotGitRepo, AlreadyInitialized,
    GitRepoNotInitialized)
from jig.plugins import (
    initializer, get_jigconfig, set_jigconfig,
    PluginManager, create_plugin, available_templates)
from jig.plugins.tools import (
    update_plugins, last_checked_for_updates, set_checked_for_updates,
    plugins_have_updates, read_plugin_list)


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
            create_plugin(
                self.plugindir, template='python',
                bundle='test', name='plugin')

    def test_creates_plugin(self):
        """
        Can create a plugin.
        """
        plugin_dir = create_plugin(
            self.plugindir, template='python',
            bundle='test', name='plugin')

        pre_commit_file = join(plugin_dir, 'pre-commit')

        # We have a pre-commit file
        self.assertTrue(isfile(pre_commit_file))

        # And it's executable
        sinfo = stat(pre_commit_file)
        self.assertTrue(S_IXUSR & sinfo.st_mode)

        config = ConfigParser()
        config.read(join(plugin_dir, 'config.cfg'))

        self.assertEqual(set(('settings', 'help', 'plugin')), set(config.sections()))
        self.assertEqual('test', config.get('plugin', 'bundle'))
        self.assertEqual('plugin', config.get('plugin', 'name'))
        self.assertEqual([], config.items('settings'))

    def test_new_plugin_compat_plugin_manager(self):
        """
        New plugins are compatible with the :py:class:`PluginManager`
        """
        plugin_dir = create_plugin(
            self.plugindir, template='python',
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

        with patch('jig.plugins.tools.git') as mock_git:
            mock_git.error = sh.ErrorReturnCode

            mock_git.return_value.pull.return_value = 'Already up to date.'

            results = update_plugins(self.gitrepodir)

        pm, value = results.items()[0]

        # We have our two plugins from the manager
        self.assertEquals(2, len(pm.plugins))

        # And it called ``git pull`` on the repository
        mock_git.return_value.pull.assert_called()


class TestPluginsHaveUpdates(PluginTestCase):

    """
    For multiple installed plugins, each can be checked for remote updates.

    """
    def setUp(self):
        plugins_dir = join(self.gitrepodir, '.jig', 'plugins')

        # Create 3 installed plugin directories. This simulates installing
        # plugins from different urls.
        for letter in 'abc':
            makedirs(join(plugins_dir, letter))

    def test_no_updates(self):
        """
        If no remote repositories have updates.
        """
        with patch('jig.plugins.tools.remote_has_updates') as rhu:
            # For each call to ``remote_has_updates``, answer False
            rhu.side_effect = [False, False, False]

            has_updates = plugins_have_updates(self.gitrepodir)

        self.assertEqual(3, rhu.call_count)
        self.assertFalse(has_updates)

    def test_has_updates(self):
        """
        If one remote repository has updates.
        """
        with patch('jig.plugins.tools.remote_has_updates') as rhu:
            # Have the last call to ``remote_has_updates`` answer True
            rhu.side_effect = [False, False, True]

            has_updates = plugins_have_updates(self.gitrepodir)

        self.assertEqual(3, rhu.call_count)
        # This time the answer is True because one plugin said it had updates
        self.assertTrue(has_updates)

    def test_all_have_updates(self):
        """
        If all repositories have updates.
        """
        with patch('jig.plugins.tools.remote_has_updates') as rhu:
            # This time they all report that they have updates
            rhu.side_effect = [True, True, True]

            has_updates = plugins_have_updates(self.gitrepodir)

        # We only need to get one True, no need to check the rest
        self.assertEqual(1, rhu.call_count)
        self.assertTrue(has_updates)


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
        config = get_jigconfig(self.gitrepodir)
        config.remove_section('jig')
        set_jigconfig(self.gitrepodir, config)

        last_check = last_checked_for_updates(self.gitrepodir)

        self.assertEqual(0, last_check)

    def test_bad_last_checked(self):
        """
        If the repo has a bad last checked value.
        """
        config = get_jigconfig(self.gitrepodir)
        config.set('jig', 'last_checked_for_updates', 'bad')
        set_jigconfig(self.gitrepodir, config)

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

    def test_already_checked_before(self):
        """
        If this is not the first time a check has been set.
        """
        set_jigconfig(self.gitrepodir,
                      config=set_checked_for_updates(self.gitrepodir))

        date1 = last_checked_for_updates(self.gitrepodir)

        set_jigconfig(self.gitrepodir,
                      config=set_checked_for_updates(self.gitrepodir))

        date2 = last_checked_for_updates(self.gitrepodir)

        self.assertEqual(date1, date2)


class TestReadPluginList(PluginTestCase):

    """
    Can read a file that will contain a list of plugin locations.

    """
    @cd_gitrepo
    def test_file_does_not_exist(self):
        """
        Specified file does not exist.
        """
        with self.assertRaises(IOError) as ec:
            read_plugin_list('not_a_file.txt')

        self.assertEqual(
            'No such file or directory',
            ec.exception[1])

    @cd_gitrepo
    def test_is_directory(self):
        """
        If the path is actually a directory.
        """
        self.commit(
            self.gitrepodir, 'a/b.txt',
            'foo\nbar\nbaz\n')

        with self.assertRaises(IOError) as ec:
            read_plugin_list('a')

        self.assertEqual(
            'Is a directory',
            ec.exception[1])

    @cd_gitrepo
    def test_reads_file(self):
        """
        Can read the file and return its contents.
        """
        self.commit(
            self.gitrepodir, 'a/b.txt',
            'foo\nbar\nbaz\n')

        plugin_list = read_plugin_list('a/b.txt')

        self.assertEqual(
            [u'foo', u'bar', u'baz'],
            plugin_list)
