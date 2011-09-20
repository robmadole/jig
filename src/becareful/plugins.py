from os import mkdir
from os.path import join, isfile
from functools import wraps
from ConfigParser import SafeConfigParser

from becareful.exc import NotGitRepo, AlreadyInitialized, GitRepoNotInitialized
from becareful.gitutils import is_git_repo, repo_bcinitialized
from becareful.conf import (BC_DIR_NAME, BC_PLUGINS_FILENAME,
    PLUGIN_CONFIG_FILENAME)


def _git_check(func):
    """
    Checks to see if the directory is a Git repo.

    Raises :py:exc:`NotGitRepo` if it's not.
    """
    @wraps(func)
    def wrapper(gitrepo):
        # Is it a Git repo?
        if not is_git_repo(gitrepo):
            raise NotGitRepo('Trying to initialize a directory that is not a '
                'Git repository.')

        return func(gitrepo)
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
    with open(join(bc_dir, BC_PLUGINS_FILENAME), 'w') as fh:
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

    with open(join(bc_dir, BC_PLUGINS_FILENAME), 'r') as fh:
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
        self._plugins = []

        # Slurp the existing config, creating any plugins we find
        for name in config.sections():
            section = Plugin(dict(config.items('section')))
            self._plugins.append(section)

    def __iter__(self):
        return iter(self._plugins)

    def __len__(self):
        return len(self._plugins)

    @property
    def plugins(self):
        return list(self)

    def add(self, plugindir):
        # Is this a plugins?
        import pdb; pdb.set_trace();
        config_filename = join(plugindir, PLUGIN_CONFIG_FILENAME)

        if not isfile(config_filename):
            raise PluginError('The plugin file {} is missing.'.format(
                config_filename))

        config = SafeConfigParser()

        with open(config_filename, 'r') as fh:
            config.readfp(fh)

        defaults = config.defaults()
        import pdb; pdb.set_trace();



class Plugin(object):

    """
    A set of functionality that interfaces with BeCareful.

    """
    def __init__(self, config={}):
        self.config = config
