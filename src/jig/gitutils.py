"""
Collection of utilities to deal with Git.
"""
import sys
from stat import S_IXUSR, S_IXGRP, S_IXOTH
from os import stat, chmod
from os.path import isdir, isfile, join, realpath, dirname

import git
import gitdb
import async
import smmap
from jig.exc import NotGitRepo, PreCommitExists
from jig.conf import BC_DIR_NAME

# Dependencies to make jig run
BE_CAREFUL_DIR = realpath(join(dirname(__file__), '..'))
GIT_PYTHON_DIR = realpath(join(dirname(git.__file__), '..'))
GITDB_DIR = realpath(join(dirname(gitdb.__file__), '..'))
ASYNC_DIR = realpath(join(dirname(async.__file__), '..'))
SMMAP_DIR = realpath(join(dirname(smmap.__file__), '..'))

PRE_COMMIT_HOOK_SCRIPT = \
"""#!{python_executable}
from sys import path
from os.path import dirname, join

# Make sure that we can find the directory that jig is installed
path.append('{be_careful_dir}')
path.append('{git_python_dir}')
path.append('{gitdb_dir}')
path.append('{async_dir}')
path.append('{smmap_dir}')

from jig.runner import Runner

# Start up the runner, passing in the repo directory
bc = Runner()
bc.fromhook(join(dirname(__file__), '..', '..'))
"""


def is_git_repo(gitdir):
    """
    Returns boolean whether the directory appears to be a Git directory.
    """
    return isdir(join(gitdir, '.git'))


def repo_bcinitialized(gitdir):
    """
    Returns boolean ``True`` if ``jig init GITDIR`` has been ran.
    """
    return isdir(join(gitdir, BC_DIR_NAME))


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
        raise NotGitRepo('{} is not a Git repository.'.format(
            gitdir))

    pc_filename = realpath(join(gitdir, '.git', 'hooks', 'pre-commit'))

    # Is there already a hook?
    if isfile(pc_filename):
        raise PreCommitExists('{} already exists and we will not overwrite '
            'it. If you want to use jig you\'ll have to sort this out '
            'yourself.'.format(pc_filename))

    script_kwargs = {
        'python_executable': sys.executable,
        'be_careful_dir': BE_CAREFUL_DIR,
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
