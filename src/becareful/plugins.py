import json
from os import mkdir
from os.path import join, isfile
from subprocess import Popen, PIPE
from functools import wraps
from ConfigParser import SafeConfigParser
from ConfigParser import Error as ConfigParserError
from ConfigParser import NoSectionError
from collections import OrderedDict

from becareful.exc import (NotGitRepo, AlreadyInitialized,
    GitRepoNotInitialized, PluginError)
from becareful.conf import (BC_DIR_NAME, BC_PLUGIN_CONFIG_FILENAME,
    BC_PLUGIN_DIR, PLUGIN_CONFIG_FILENAME, PLUGIN_PRE_COMMIT_SCRIPT)
from becareful.gitutils import is_git_repo, repo_bcinitialized
from becareful.diffconvert import GitDiffIndex


def _git_check(func):
    """
    Checks to see if the directory is a Git repo.

    Raises :py:exc:`NotGitRepo` if it's not.

    You can only use this decorator on a function where the first argument is
    the path to the Git repository.
    """
    @wraps(func)
    def wrapper(gitrepo, *args, **kwargs):
        # Is it a Git repo?
        if not is_git_repo(gitrepo):
            raise NotGitRepo('Trying to initialize a directory that is not a '
                'Git repository.')

        return func(gitrepo, *args, **kwargs)
    return wrapper


@_git_check
def initializer(gitrepo):
    """
    Initializes a Git repo for use with BeCareful.

    This will create a directory in the root of the Git repo that will contain
    files (plugins) and configuration.
    """
    # If it's already initialized, refuse to run
    if repo_bcinitialized(gitrepo):
        raise AlreadyInitialized('The repository is already initialized.')

    # Create the container for all things BeCareful
    bc_dir = join(gitrepo, BC_DIR_NAME)

    mkdir(bc_dir)
    mkdir(join(bc_dir, BC_PLUGIN_DIR))

    return set_bcconfig(gitrepo)


@_git_check
def set_bcconfig(gitrepo, config=None):
    """
    Saves the config for BeCareful in the Git repo.

    The ``config`` argument must be an instance of :py:class:`ConfigParser`.
    """
    # If it's already initialized, refuse to run
    if not repo_bcinitialized(gitrepo):
        raise GitRepoNotInitialized('The repository has not been initialized.')

    # Create the container for all things BeCareful
    bc_dir = join(gitrepo, BC_DIR_NAME)

    # Create an empty config parser if we were not passed one
    plugins = config if config else SafeConfigParser()

    # Create a plugin list file
    with open(join(bc_dir, BC_PLUGIN_CONFIG_FILENAME), 'w') as fh:
        plugins.write(fh)

        return plugins


@_git_check
def get_bcconfig(gitrepo):
    """
    Gets the config for a BeCareful initialized Git repo.
    """
    bc_dir = join(gitrepo, BC_DIR_NAME)

    if not repo_bcinitialized(gitrepo):
        raise GitRepoNotInitialized('This repository has not been initialized')

    with open(join(bc_dir, BC_PLUGIN_CONFIG_FILENAME), 'r') as fh:
        plugins = SafeConfigParser()
        plugins.readfp(fh)

        return plugins


class PluginManager(object):

    """
    Provides access to running and managing plugins.

    """
    def __init__(self, config):
        """
        Create a plugin manager with the given ``config``.

        The ``config`` argument should be an instance of
        :py:class:`SafeConfigParser` and will be the main configuration for an
        BeCareful-initialized Git repository.
        """
        # The instance of SafeConfigParser we get from :py:method:`config`.
        self.config = config

        # Look through the config and initialize any installed plugins
        self._plugins = self._init_plugins(config)

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
                    plugin_config.readfp(fh)
                except ConfigParserError:
                    # Something happened when parsing the config
                    raise PluginError('Could not parse config file for '
                        '{} in {}'.format(name, path))

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
        Add the given plugin to this manager instance.

        ``plugindir`` should be the full path to a directory containing all the
        files required for a BeCareful plugin.
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
                '[plugin] section')

        try:
            bundle = plugin_info['bundle']
            name = plugin_info['name']
        except KeyError:
            raise PluginError('Could not find the bundle or name of '
                'the plugin')

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
        self.path = path
        # Plugin-specific configuration
        self.config = config

    def pre_commit(self, git_diff_index):
        """
        Runs the plugin's pre-commit script, passing in the diff.

        ``git_diff_index`` is a :py:class:`becareful.diffconvert.GitDiffIndex`
        object.

        The pre-commit script will receive JSON data as standard input (stdin).
        The JSON data is comprised of two main attributes: config and diff.

        The ``config`` attribute represents the configuration for this plugin.
        This is up to the plugin author but the values can be changed by the
        user.

        The ``diff`` attribute is a list of files and changes that have
        occurred to them.  See :py:module:`becareful.diffconvert` for
        information on what this object provides.
        """
        # Grab this plugin's settings
        data_in = {
            'config': self.config,
            'files': git_diff_index}

        script = join(self.path, PLUGIN_PRE_COMMIT_SCRIPT)
        ph = Popen([script], stdin=PIPE, stdout=PIPE, stderr=PIPE)

        # Send the data to the script
        stdout, stderr = ph.communicate(
            json.dumps(data_in, indent=2, cls=PluginDataJSONEncoder))

        retcode = ph.returncode

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
        if isinstance(obj, GitDiffIndex):
            files = [i for i in obj.files()]

            obj = []
            for f in files:
                obj.append({
                    'type': f['type'],
                    'name': f['name'],
                    'filename': f['filename'],
                    'diff': [j for j in f['diff']]})

            return obj
        return super(PluginDataJSONEncoder, self).default(obj)
