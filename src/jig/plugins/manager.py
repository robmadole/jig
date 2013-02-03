import json
from os import listdir
from os.path import join, isfile, isdir, realpath
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from ConfigParser import Error as ConfigParserError
from ConfigParser import NoSectionError
from collections import OrderedDict

from jig.exc import PluginError
from jig.conf import PLUGIN_CONFIG_FILENAME, PLUGIN_PRE_COMMIT_SCRIPT


class PluginManager(object):

    """
    Provides access to running and managing plugins.

    """
    def __init__(self, config=None):
        """
        Create a plugin manager with the given ``config``.

        The ``config`` argument should be an instance of
        :py:class:`SafeConfigParser` and will be the main configuration for an
        jig-initialized Git repository.

        If ``config`` is missing, an empty :py:class:`SafeConfigParser` will be
        created.
        """
        # The instance of SafeConfigParser we get from :py:method:`config`.
        self.config = config or SafeConfigParser()

        # Look through the config and initialize any installed plugins
        self._plugins = self._init_plugins(self.config)

    def _init_plugins(self, config):
        """
        Creates :py:class:`Plugin` instances from ``config``.
        """
        plugins = []
        for section_name in config.sections():
            if not section_name.startswith('plugin:'):
                # We are only interested in the plugin configs
                continue

            _, bundle, name = section_name.split(':')

            path = config.get(section_name, 'path')

            plugin_cfg = join(path, PLUGIN_CONFIG_FILENAME)

            with open(plugin_cfg) as fh:
                plugin_config = SafeConfigParser()
                try:
                    plugin_config.readfp(fh)   # pragma: no branch
                except ConfigParserError:
                    # Something happened when parsing the config
                    raise PluginError('Could not parse config file for '
                        '{} in {}.'.format(name, path))

            # Get rid of the path, we don't need to send this as part of the
            # config for the plugin
            pc = OrderedDict(config.items(section_name))
            del pc['path']

            section = Plugin(bundle, name, path, pc)
            plugins.append(section)

        return plugins

    def __iter__(self):
        return iter(self._plugins)

    def __len__(self):
        return len(self._plugins)

    @property
    def plugins(self):
        return list(self)

    def add(self, plugindir):
        """
        Add the given plugin or directory of plugins to this manager instance.

        ``plugindir`` should be the full path to a directory containing all the
        files required for a Jig plugin. It can alternatively be a directory of
        plugins, where each sub-directory is a Jig plugin.

        If ``recursive`` is True, then add will treat this as a directory of
        plugins instead of a single plugin and attempt to add them all.

        Returns a list of plugins that were added to this manager.
        """
        exc_collection = []
        added = []

        try:
            # Add as if plugindir is the actual plugin
            added.append(self._add_plugin(plugindir))

            return added
        except PluginError as pe:
            exc_collection.append(pe)

        # Walk the directory, try to add each sub-directory as a plugin
        for dirname in listdir(plugindir):
            subdir = join(plugindir, dirname)
            if not isdir(subdir):
                continue
            try:
                added.append(self._add_plugin(subdir))
            except PluginError as pe:
                exc_collection.append(pe)

        if added:
            return added

        # If we haven't added any plugins and we have an exception raise it
        raise exc_collection[0]

    def _add_plugin(self, plugindir):
        """
        If this is a Jig plugin, add it.

        ``plugindir`` should be the full path to a directory containing all the
        files required for a jig plugin.
        """
        # Is this a plugins?
        config_filename = join(plugindir, PLUGIN_CONFIG_FILENAME)

        if not isfile(config_filename):

            raise PluginError('The plugin file {} is missing.'.format(
                config_filename))

        config = SafeConfigParser()

        with open(config_filename, 'r') as fh:
            try:
                config.readfp(fh)
            except ConfigParserError as e:
                raise PluginError(e)

        try:
            settings = OrderedDict(config.items('settings'))
        except NoSectionError:
            settings = []

        try:
            plugin_info = OrderedDict(config.items('plugin'))
        except NoSectionError:
            raise PluginError('The plugin config does not contain a '
                '[plugin] section.')

        try:
            bundle = plugin_info['bundle']
            name = plugin_info['name']
        except KeyError:
            raise PluginError('Could not find the bundle or name of '
                'the plugin.')

        new_section = 'plugin:{bundle}:{name}'.format(
            bundle=bundle, name=name)

        if self.config.has_section(new_section):
            raise PluginError('The plugin is already installed.')

        self.config.add_section(new_section)

        self.config.set(new_section, 'path', plugindir)

        for setting in settings:
            option, value = setting, settings[setting]
            self.config.set(new_section, option, value)

        # Re-initialize the self.plugins list
        self._plugins = self._init_plugins(self.config)

        # And return the plugin once we find it
        for plugin in self._plugins:   # pragma: no branch
            if plugin.name == name and plugin.bundle == bundle:
                return plugin

    def remove(self, bundle, name):
        """
        Remove a plugin from the list and config.

        Both ``bundle`` and ``name`` are required. A
        :py:exception:`PluginError` will be raised if the plugin does not
        exist.
        """
        section_name = 'plugin:{bundle}:{name}'.format(
            bundle=bundle, name=name)

        if not self.config.has_section(section_name):
            raise PluginError('This plugin does not exist.')

        self.config.remove_section(section_name)

        # Again, re-initialize the self.plugins list
        self._plugins = self._init_plugins(self.config)


class Plugin(object):

    """
    A single unit that performs some helpful operation for the user.

    """
    def __init__(self, bundle, name, path, config={}):
        # What bundle is this plugin a part of
        self.bundle = bundle
        # What is the name of this plugin?
        self.name = name
        # Where does this plugin live
        self.path = realpath(path)
        # Plugin-specific configuration
        self.config = config

    def pre_commit(self, git_diff_index):
        """
        Runs the plugin's pre-commit script, passing in the diff.

        ``git_diff_index`` is a :py:class:`jig.diffconvert.GitDiffIndex`
        object.

        The pre-commit script will receive JSON data as standard input (stdin).
        The JSON data is comprised of two main attributes: config and diff.

        The ``config`` attribute represents the configuration for this plugin.
        This is up to the plugin author but the values can be changed by the
        user.

        The ``diff`` attribute is a list of files and changes that have
        occurred to them.  See :py:module:`jig.diffconvert` for
        information on what this object provides.
        """
        # Grab this plugin's settings
        data_in = {
            'config': self.config,
            'files': git_diff_index}

        script = join(self.path, PLUGIN_PRE_COMMIT_SCRIPT)
        ph = Popen([script], stdin=PIPE, stdout=PIPE, stderr=PIPE)

        # Send the data to the script
        stdin = json.dumps(data_in, indent=2, cls=PluginDataJSONEncoder)

        retcode = None
        stdout = ''
        stderr = ''

        try:
            stdout, stderr = ph.communicate(stdin)

            # Convert to unicode
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')

            retcode = ph.returncode
        except OSError as ose:
            # Generic non-zero retcode that indicates an error
            retcode = 1
            if ose.errno == 32:
                stderr = u'Error: received SIGPIPE from the command'
            else:
                stderr = unicode(ose)

        # And return the relevant stuff
        return retcode, stdout, stderr


class PluginDataJSONEncoder(json.JSONEncoder):

    """
    Converts the special data objects used when a plugin runs pre-commit.

    """
    def default(self, obj):
        """
        Implements JSONEncoder default method.
        """
        files = [i for i in obj.files()]

        obj = []
        for f in files:
            obj.append({
                'type': unicode(f['type']),
                'name': unicode(f['name']),
                'filename': unicode(f['filename']),
                'diff': [j for j in f['diff']]})

        return obj
