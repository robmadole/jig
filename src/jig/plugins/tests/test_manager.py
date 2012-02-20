import json
from os.path import join

from jig.tests.testcase import PluginTestCase
from jig.exc import PluginError
from jig.plugins import PluginManager


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

    def test_add_plugin(self):
        """
        Test the add method on the plugin manager.
        """
        # Config is empty
        pm = PluginManager(self.bcconfig)

        plugin = pm.add(join(self.fixturesdir, 'plugin01'))

        self.assertEqual(1, len(pm.plugins))
        self.assertTrue(pm.config.has_section('plugin:test01:plugin01'))
        self.assertEqual('plugin01', plugin.name)
        self.assertEqual('test01', plugin.bundle)

    def test_could_not_parse(self):
        """
        Tests a bad plugin config from the main config.
        """
        self._add_plugin(self.bcconfig, 'plugin02')

        with self.assertRaises(PluginError) as ec:
            PluginManager(self.bcconfig)

        self.assertIn('Could not parse config file', str(ec.exception))

    def test_contains_parsing_errors(self):
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

    def test_remove_plugin(self):
        """
        Remove a plugin.
        """
        pm = PluginManager(self.bcconfig)

        pm.add(join(self.fixturesdir, 'plugin01'))

        self.assertTrue(pm.config.has_section('plugin:test01:plugin01'))

        pm.remove('test01', 'plugin01')

        self.assertFalse(pm.config.has_section('plugin:test01:plugin01'))
        self.assertEqual([], pm.plugins)

    def test_remove_non_existent_section(self):
        """
        Try to remove a plugin that does not exist.
        """
        pm = PluginManager(self.bcconfig)

        with self.assertRaises(PluginError) as ec:
            pm.remove('bundle', 'name')

        self.assertEqual('This plugin does not exist.',
            str(ec.exception))


class TestPlugin(PluginTestCase):

    """
    Test the individual plugins.

    """
    def setUp(self):
        super(TestPlugin, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.testrepo = repo
        self.testrepodir = working_dir
        self.testdiffs = diffs

    def test_new_file_pre_commit(self):
        """
        Test a new file pre-commit.
        """
        pm = PluginManager(self.bcconfig)

        pm.add(join(self.fixturesdir, 'plugin01'))
        gdi = self.git_diff_index(self.testrepo, self.testdiffs[0])

        retcode, stdout, stderr = pm.plugins[0].pre_commit(gdi)

        data = json.loads(stdout)

        # Everything should have gone splendidly
        self.assertEqual(0, retcode)
        # Should contain our file that was added
        self.assertIn('argument.txt', data)
        # And our first line should be a warning
        self.assertEqual(
            [1, u'warn', u'The cast: is +'],
            data['argument.txt'][0])
