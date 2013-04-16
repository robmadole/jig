# coding=utf-8
from os.path import join
from tempfile import mkdtemp
from ConfigParser import SafeConfigParser

from jig.tests.testcase import (
    CommandTestCase, PluginTestCase,
    cd_gitrepo, result_with_hint)
from jig.commands import config
from jig.exc import ForcedExit
from jig.plugins import (
    set_jigconfig, get_jigconfig, create_plugin,
    PluginManager)
from jig.commands.hints import (
    NO_PLUGINS_INSTALLED, CHANGE_PLUGIN_SETTINGS, INVALID_CONFIG_KEY)


class TestPluginCommand(CommandTestCase, PluginTestCase):

    """
    Test the plugin command.

    """
    command = config.Command

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

    def _clear_settings(self, gitrepodir):
        """
        Remove all plugin specific settings.
        """
        config = get_jigconfig(self.gitrepodir)
        pm = PluginManager(config)

        for section in pm.config.sections():
            if not section.startswith('plugin'):
                continue
            for option, value in pm.config.items(section):
                if option == 'path':
                    continue
                pm.config.remove_option(section, option)

        set_jigconfig(self.gitrepodir, pm.config)

    def _set(self, gitrepodir, bundle_name, plugin_name, key, value):
        """
        Change a setting for a plugin and save the Jig config.
        """
        config = get_jigconfig(self.gitrepodir)
        pm = PluginManager(config)

        pm.config.set(
            'plugin:{0}:{1}'.format(bundle_name, plugin_name),
            key, value)

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

    def test_list_settings(self):
        """
        List settings from freshly installed plugins.

        The default plugin config and the plugins.cfg will be in sync.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01', settings={
                'a': '1', 'b': '2', 'c': '3'}))
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test02', name='plugin02', settings={
                'a': '11', 'b': '22', 'c': '33'}))

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(
            result_with_hint(
                u'''
                test01.plugin01.a=1
                test01.plugin01.b=2
                test01.plugin01.c=3
                test02.plugin02.a=11
                test02.plugin02.b=22
                test02.plugin02.c=33
                ''',
                CHANGE_PLUGIN_SETTINGS),
            self.output)

    def test_list_plugins_no_overridden_config(self):
        """
        Lists settings if there are no overridden configs.

        The default plugin settings will not be in plugins.cfg.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01', settings={
                'a': '1', 'b': '2', 'c': '3'}))

        self._clear_settings(self.gitrepodir)

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(
            result_with_hint(
                u'''
                test01.plugin01.a=1
                test01.plugin01.b=2
                test01.plugin01.c=3
                ''',
                CHANGE_PLUGIN_SETTINGS),
            self.output)

    def test_list_plugins_one_overridden_config(self):
        """
        Lists settings if there is one overridden setting.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01', settings={
                'a': '1', 'b': '2', 'c': '3'}))

        self._clear_settings(self.gitrepodir)

        # Override the setting for this plugin, it should take the place of the
        # default which is '1'
        self._set(self.gitrepodir, 'test01', 'plugin01', 'a', 'one')

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(
            result_with_hint(
                u'''
                test01.plugin01.a=one
                test01.plugin01.b=2
                test01.plugin01.c=3
                ''',
                CHANGE_PLUGIN_SETTINGS),
            self.output)

    def test_list_missing_settings_on_plugin(self):
        """
        If the installed plugin is missing settings.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01'))

        plugin_config_filename = join(
            self.plugindir, 'plugin01', 'config.cfg')

        with open(plugin_config_filename, 'r') as fh:
            config = SafeConfigParser()
            config.readfp(fh)

        # What if this plugin has no settings whatsoever, perhaps the plugin
        # author just didn't have any and did not include that section
        config.remove_section('settings')

        with open(plugin_config_filename, 'w') as fh:
            config.write(fh)

        self.run_command('list -r {0}'.format(self.gitrepodir))

        self.assertResults(result_with_hint(
            u'''
            Installed plugins have no settings.
            ''',
            CHANGE_PLUGIN_SETTINGS),
            self.output)

    def test_config_set_plugin_not_found(self):
        """
        Setting cannot be changed because plugin is not installed.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01'))

        # plugin01 is installed but not the following
        with self.assertRaises(ForcedExit):
            self.run_command('set -r {0} notbundle.notplugin.a 111'.format(
                self.gitrepodir))

        self.assertResults(
            u'Could not locate plugin notplugin.',
            self.error)

    def test_config_invalid_key(self):
        """
        Invalid keys are handled.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01'))

        with self.assertRaises(ForcedExit):
            self.run_command('set -r {0} a:b:c 111'.format(self.gitrepodir))

        self.assertResults(result_with_hint(
            u'''
            a:b:c is an invalid config key.
            ''',
            INVALID_CONFIG_KEY),
            self.error)

    def test_config_set(self):
        """
        Setting can be changed.
        """
        self._add_plugin(create_plugin(
            self.plugindir, template='python',
            bundle='test01', name='plugin01', settings={
                'a': '1', 'b': '2', 'c': '3'}))

        self.run_command(
            'set -r {0} test01.plugin01.a 111'.format(self.gitrepodir))

        # Setting was changed, no output to the console
        self.assertEqual('', self.output)

        # The setting was changed
        config = get_jigconfig(self.gitrepodir)

        self.assertEqual('111', config.get('plugin:test01:plugin01', 'a'))
