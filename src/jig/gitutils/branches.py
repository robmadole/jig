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


def parse_rev_range(repository, rev_range):
    """
    Convert revision range to two :class:`git.objects.commit.Commit` objects.

    :param string repository: path to the Git repository
    :param string rev_range: Double dot-separated revision range, like "FOO..BAR"
    :returns: the two commits representing the range
    :rtype: tuple
    """
    rev_pair = rev_range.split('..')

    if len(rev_pair) != 2 or not all(rev_pair):
        raise GitRevListFormatError(rev_range)

    rev_a, rev_b = rev_pair

    try:
        repo = git.Repo(repository)

        commit_a = repo.commit(rev_a)
        commit_b = repo.commit(rev_b)

        return commit_a, commit_b
    except (BadObject, GitCommandError):
        raise GitRevListMissing(rev_range)
