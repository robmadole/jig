from os import mkdir
from os.path import join
from ConfigParser import SafeConfigParser

from becareful.exc import NotGitRepo, AlreadyInitialized
from becareful.gitutils import is_git_repo, repo_bcinitialized
from becareful.conf import BC_DIR_NAME, PLUGINS_FILENAME


def initializer(gitrepo):
    """
    Initializes a Git repo for use with BeCareful.

    This will create a directory in the root of the Git repo that will contain
    files (plugins) and configuration.
    """
    # Is it a Git repo?
    if not is_git_repo(gitrepo):
        raise NotGitRepo('Trying to initialize a directory that is not a '
            'Git repository.')

    # If it's already initialized, refuse to run
    if repo_bcinitialized(gitrepo):
        raise AlreadyInitialized('The repository is already initialized.')

    # Create the container for all things BeCareful
    bc_dir = join(gitrepo, BC_DIR_NAME)

    mkdir(bc_dir)

    # Create a plugin list file
    with open(join(bc_dir, PLUGINS_FILENAME), 'w') as fh:
        plugins = SafeConfigParser()

        plugins.write(fh)

        return plugins
