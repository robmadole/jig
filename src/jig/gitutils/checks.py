from os.path import isdir, join

from jig.conf import JIG_DIR_NAME


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


def working_directory_dirty(gitdir):
    """
    Returns boolean indicating if the working directory is dirty.
    """
    repo = Repo(gitdir)

    return repo.is_dirty()
