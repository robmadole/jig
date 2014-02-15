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


def is_git_repo(gitdir):
    """
    Returns boolean whether the directory appears to be a Git directory.
    """
    return isdir(join(gitdir, '.git'))


def repo_jiginitialized(gitdir):
    """
    Returns boolean ``True`` if ``jig init GITDIR`` has been ran.
    """
    return isdir(join(gitdir, JIG_DIR_NAME))
