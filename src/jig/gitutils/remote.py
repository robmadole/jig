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

# Dependencies to make jig run
JIG_DIR = realpath(join(dirname(__file__), '..'))
GIT_PYTHON_DIR = realpath(join(dirname(git.__file__), '..'))
GITDB_DIR = realpath(join(dirname(gitdb.__file__), '..'))
ASYNC_DIR = realpath(join(dirname(async.__file__), '..'))
SMMAP_DIR = realpath(join(dirname(smmap.__file__), '..'))


def clone(repository, to_dir, branch=None):
    """
    Clone a Git repository to a directory.

    Where ``repository`` is a string representing a path or URL to the
    repository and ``to_dir`` is where the repository will be cloned.

    :param string repository: path or URL to the repository to clone
    :param string todir: where to clone the repository to
    :param string branch: branch to checkout instead of the repository's
        default
    """
    gitobj = git.Git()

    try:
        cmd = ['git', 'clone']

        if branch:
            cmd.extend(['--branch', branch])

        cmd.extend([repository, to_dir])

        gitobj.execute(cmd)

        return gitobj
    except git.GitCommandError as gce:
        raise GitCloneError(str(gce))


def remote_has_updates(repository):
    """
    Fetches the remote and check for available updates.

    :param string repository: path to the Git repository
    """
    try:
        repo = git.Repo(repository)

        # Get the latest tree from all remotes
        [i.fetch() for i in repo.remotes]

        active = repo.active_branch
        tracking = repo.active_branch.tracking_branch()

        is_different = active.commit != tracking.commit
        is_tracking_newer = \
            tracking.commit.committed_date > active.commit.committed_date
    except (AttributeError, GitCommandError, AssertionError):
        # The Python Git library issues some strange errors during
        # a fetch on occasion, so this "diaper"ish except is intended
        # to allow the process to continue without failing with a traceback.

        # Let the result be that new commits are available even though we had
        # an error. During a fetch this is typically the case.
        is_different = True
        is_tracking_newer = True

    return is_different and is_tracking_newer
