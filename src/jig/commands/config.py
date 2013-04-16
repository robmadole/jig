import argparse
from os.path import join
from ConfigParser import SafeConfigParser
from collections import namedtuple
from textwrap import TextWrapper

from jig.conf import PLUGIN_CONFIG_FILENAME
from jig.exc import CommandError, ConfigKeyInvalid
from jig.commands.base import BaseCommand, plugins_by_bundle
from jig.commands.hints import NO_PLUGINS_INSTALLED, CHANGE_PLUGIN_SETTINGS
from jig.plugins import (
    get_jigconfig, set_jigconfig, PluginManager)

_parser = argparse.ArgumentParser(
    description='Manage settings for installed Jig plugins',
    usage='jig config [-h] ACTION')

_subparsers = _parser.add_subparsers(
    title='actions',
    description='available commands to manage settings')

_listparser = _subparsers.add_parser(
    'list', help='list all settings',
    usage='jig config list [-h] [-r GITREPO]')
_listparser.add_argument(
    '--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_listparser.set_defaults(subcommand='list')

_aboutparser = _subparsers.add_parser(
    'about', help='learn about a plugin\'s settings',
    usage='jig config about [-h] [-r GITREPO]')
_aboutparser.add_argument(
    '--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_aboutparser.set_defaults(subcommand='about')

_setparser = _subparsers.add_parser(
    'set', help='set a single setting for an installed plugin',
    usage='jig config set [-h] [-r GITREPO] KEY VALUE')
_setparser.add_argument(
    '--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_setparser.add_argument(
    'key',
    help='Setting key which is a dot-separated string of the '
    'bundle name, plugin name, and setting name')
_setparser.add_argument(
    'value',
    help='Value for the specified settings')
_setparser.set_defaults(subcommand='set')


try:
    from collections import OrderedDict
except ImportError:   # pragma: no cover
    from ordereddict import OrderedDict


def _get_plugin_config_section(plugin_dir, section):
    """
    Get a section of a plugin's config.

    :param string plugin_dir: the directory where the plugin's config can be found
    :param string section: name of the section to fetch
    :rtype: OrderedDict
    :returns: section of a config
    """
    config_filename = join(plugin_dir, PLUGIN_CONFIG_FILENAME)

    with open(config_filename, 'r') as fh:
        config = SafeConfigParser()
        config.readfp(fh)

        if not config.has_section(section):
            return OrderedDict()
        return OrderedDict(config.items(section))


SettingsMeta = namedtuple('SettingsMeta', 'plugin key value default about')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        subcommand = argv.subcommand

        # Handle the actions
        getattr(self, subcommand)(argv)

    def _has_plugin(self, pm, bundle_name, plugin_name):
        """
        Check if a plugin is installed.

        :param string bundle_name: the name of the bundle
        :param string plugin_name: name of the plugin
        :returns: True if it is installed, False if not
        :rtype: bool
        """
        for plugin in pm.plugins:
            if plugin.name == plugin_name and plugin.bundle == bundle_name:
                return True
        return False

    def _settings(self, pm):
        """
        Sorted iteratable of meta information for a plugin setting

        :returns: named tuple of (plugin, setting key, and setting value,
            default value, and about/help message).
        """
        bundles = plugins_by_bundle(pm)

        # Gather up all the settings sorted by plugin and then setting
        sort_bundles = sorted(bundles.items(), key=lambda b: b[0])

        for name, plugins in sort_bundles:
            sort_plugins = sorted(plugins, key=lambda p: p.name)

            for plugin in sort_plugins:
                # Configuration from the plugins.cfg file, not the plugin
                # defaults
                local_config = OrderedDict(plugin.config.items())

                # Get the plugin defaults in case they've changed or vanished
                # from plugins.cfg
                default_config = _get_plugin_config_section(
                    plugin.path, 'settings')

                # About/help messages for the settings
                settings_about = _get_plugin_config_section(
                    plugin.path, 'help')

                # Merge the settings together letting the local settings
                # override the default
                merged_config = OrderedDict()
                merged_config.update(default_config)
                merged_config.update(local_config)

                sort_config = sorted(merged_config.items(), key=lambda s: s[0])

                for key, value in sort_config:
                    yield SettingsMeta(
                        plugin, key, value,
                        default_config.get(key, None),
                        settings_about.get(key, None))

    def list(self, argv):
        """
        List the current settings for all plugins.
        """
        path = argv.path

        with self.out() as out:
            config = get_jigconfig(path)

            pm = PluginManager(config)

            if not pm.plugins:
                out.append(u'No plugins installed.')
                out.extend(NO_PLUGINS_INSTALLED)
                return

            for meta in self._settings(pm):
                out.append(u'{bundle}.{plugin}.{config_key}={config_value}'.format(
                    bundle=meta.plugin.bundle, plugin=meta.plugin.name,
                    config_key=meta.key, config_value=meta.value))

            if not out:
                out.append(u'Installed plugins have no settings.')

            out.extend(CHANGE_PLUGIN_SETTINGS)

    def about(self, argv):
        """
        Provide about/help on each plugin setting.
        """
        path = argv.path

        def wrap(payload):
            indent = '   '
            tw = TextWrapper(
                width=70,
                initial_indent=indent,
                subsequent_indent=indent)
            return u'\n'.join(tw.wrap(payload))

        with self.out() as out:
            config = get_jigconfig(path)

            pm = PluginManager(config)

            if not pm.plugins:
                out.append(u'No plugins installed.')
                out.extend(NO_PLUGINS_INSTALLED)
                return

            for meta in self._settings(pm):
                out.append(u'{bundle}.{plugin}.{config_key}'.format(
                    bundle=meta.plugin.bundle, plugin=meta.plugin.name,
                    config_key=meta.key))
                out.append(u'(default: {0})'.format(meta.default))

                if meta.about:
                    out.append(wrap(meta.about.strip()))

                out.append(u'')

            if not out:
                out.append(u'Installed plugins have no settings.')

    def set(self, argv):
        """
        Change a single setting for an installed plugin.
        """
        path = argv.path
        key = argv.key
        key_parts = key.split('.', 3)
        config_value = argv.value

        with self.out():
            if len(key_parts) != 3:
                # The key is not correct
                raise ConfigKeyInvalid(
                    '{0} is an invalid config key.'.format(key))

            # Unpack our dot-separated string into the components identifying a setting
            bundle, plugin, config_key = key_parts

            config = get_jigconfig(path)

            pm = PluginManager(config)

            if not self._has_plugin(pm, bundle, plugin):
                raise CommandError('Could not locate plugin {0}.'.format(
                    plugin))

            section_name = 'plugin:{0}:{1}'.format(
                bundle, plugin)

            # Finally change the setting
            pm.config.set(section_name, config_key, config_value)

            set_jigconfig(path, pm.config)
