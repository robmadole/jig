"""
Collection of utilities to deal with Git.
"""
from os.path import isdir, isfile, join, realpath, dirname

from becareful.exc import NotGitRepo, PreCommitExists

# Where is BeCareful installed?
BE_CAREFUL_DIR = realpath(join(dirname(__file__), '..'))

PRE_COMMIT_HOOK_SCRIPT = """
#!{python_executable}
from sys import path
from os.path import dirname, join

# Make sure that we can find the directory that BeCareful is installed
path.append('{be_careful_dir}')

from becareful import runner

# Start up the runner, passing in the repo directory
runner.fromhook(join(dirname(__file__), '..', '..'))
"""


def hook(gitdir):
    """
    Places a pre-commit hook in the given directory.

    The hook will be configured to run using the version of Python that was
    used to install BeCareful.

    Returns the full path to the 
    Raises :py:exc:`NotGitRepo` if the directory given is not a Git repository.
    Raises :py:exc:`PreCommitExists` if there is already a Git hook for
    pre-commit present.
    """
    if not isdir(join(gitdir, '.git')):
        raise NotGitRepo('{} is not a git repository.'.format(
            gitdir))

    pc_filename = join(gitdir, '.git', 'hooks', 'pre-commit')

    # Is there already a hook?
    if isfile(pc_filename):
        raise PreCommitExists('{} already exists and we will not overwrite '
            'it. If you want to use BeCareful you\'ll have to sort this out '
            'yourself.')

    return realpath(pc_filename)
