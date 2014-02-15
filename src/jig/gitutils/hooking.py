import sys
from stat import S_IXUSR, S_IXGRP, S_IXOTH
from os import stat, chmod
from os.path import isdir, isfile, join, realpath, dirname
from textwrap import dedent

import git
from git.exc import GitCommandError, BadObject
import gitdb
import async
import smmap

from jig.exc import (
    NotGitRepo, PreCommitExists, GitCloneError, GitRevListFormatError,
    GitRevListMissing)
from jig.conf import JIG_DIR_NAME
from jig.gitscripts import PRE_COMMIT_HOOK_SCRIPT, AUTO_JIG_INIT_SCRIPT
from jig.gitutils.checks import is_git_repo

# Dependencies to make jig run
JIG_DIR = realpath(join(dirname(__file__), '..'))
GIT_PYTHON_DIR = realpath(join(dirname(git.__file__), '..'))
GITDB_DIR = realpath(join(dirname(gitdb.__file__), '..'))
ASYNC_DIR = realpath(join(dirname(async.__file__), '..'))
SMMAP_DIR = realpath(join(dirname(smmap.__file__), '..'))

# Possible locations of the shared Git templates directory
GIT_TEMPLATES_SEARCH_LOCATIONS = [
    '/usr/share/git-core/templates',
    '/usr/local/share/git-core/templates',
    '/usr/local/git/share/git-core/templates'
]


def hook(gitdir):
    """
    Places a pre-commit hook in the given directory.

    The hook will be configured to run using the version of Python that was
    used to install jig.

    Returns the full path to the newly created post-commit hook.

    Raises :py:exc:`NotGitRepo` if the directory given is not a Git repository.
    Raises :py:exc:`PreCommitExists` if there is already a Git hook for
        pre-commit present.
    """
    if not is_git_repo(gitdir):
        raise NotGitRepo('{0} is not a Git repository.'.format(
            gitdir))

    pc_filename = realpath(join(gitdir, '.git', 'hooks', 'pre-commit'))

    # Is there already a hook?
    if isfile(pc_filename):
        raise PreCommitExists('{0} already exists'.format(pc_filename))

    script_kwargs = {
        'python_executable': sys.executable,
        'jig_dir': JIG_DIR,
        'git_python_dir': GIT_PYTHON_DIR,
        'gitdb_dir': GITDB_DIR,
        'async_dir': ASYNC_DIR,
        'smmap_dir': SMMAP_DIR}

    with open(pc_filename, 'w') as fh:
        fh.write(PRE_COMMIT_HOOK_SCRIPT.format(**script_kwargs))

    sinfo = stat(pc_filename)
    mode = sinfo.st_mode | S_IXUSR | S_IXGRP | S_IXOTH

    # Make sure it's executable
    chmod(pc_filename, mode)

    return pc_filename


def create_auto_init_templates(user_home_directory):
    """
    Creates a Git templates directory with a Jig auto-init pre-commit hook 

    The templates directory will be created in the user's home directory inside
    a ~/.jig main directory.

    An attempt will be made to find the shared, global Git templates directory
    and copy it. An exception will be thrown if it cannot be found.

    :param string user_home_directory: Full path to the user's home directory
    """
    # Create the .jig directory in the home directory

    # Copy the shared Git templates directory to .jig/git/templates
    pass


def set_templates_directory(gitconfig, templates_directory):
    """
    Sets the template directory in the given ``gitconfig``.
    """
    # Load up the config

    # Add the [init] section if it's not here

    # Set templatedir to the templates directory
    pass
