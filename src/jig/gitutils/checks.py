from os.path import isdir, join

from gitdb.db import LooseObjectDB

from jig.conf import JIG_DIR_NAME
from jig.gitutils.commands import git


def is_git_repo(gitdir):
    """
    Returns boolean whether the directory appears to be a Git directory.
    """
    return isdir(join(gitdir, '.git'))


def is_empty_git_repo(gitdir):
    """
    Determine if there are no objects in the Git database.
    """
    if not is_git_repo(gitdir):
        return True

    db = LooseObjectDB(join(gitdir, '.git', 'objects'))

    return db.size() == 0


def repo_jiginitialized(gitdir):
    """
    Returns boolean ``True`` if ``jig init GITDIR`` has been ran.
    """
    return isdir(join(gitdir, JIG_DIR_NAME))


def repo_is_dirty(
    gitdir,
    index=True,
    working_directory=True,
    untracked_files=False
):
    """
    Determine if a repository is dirty by having local modifications.
    """
    dirty = []

    default_args = ('--abbrev=40', '--full-index', '--raw')

    if index:
        dirty.append(
            len(git(gitdir).diff('--cached', *default_args))
        )

    if working_directory:
        dirty.append(
            len(git(gitdir).diff(*default_args))
        )

    if untracked_files:
        dirty.append(
            len(git(gitdir)(
                'ls-files',
                '--other',
                '--directory',
                '--exclude-standard'
            ))
        )

    return any(dirty)
