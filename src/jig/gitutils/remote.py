from datetime import datetime

from jig.exc import GitCloneError
from jig.gitutils.commands import git


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
    try:
        cmd = ['clone']

        if branch:
            cmd.extend(['--branch', branch])

        cmd.extend([repository, to_dir])

        git()(*cmd)

        return True
    except git.error as e:
        raise GitCloneError(str(e.stderr))


def _datetime_of_commit(repository, commit):
    return datetime.fromtimestamp(
        int(git(repository).show('-s', '--format=%ct', commit).strip())
    )


def remote_has_updates(repository):
    """
    Fetches the remote and check for available updates.

    :param string repository: path to the Git repository
    """
    try:
        git_bound = git(repository)

        # Get the latest tree from all remotes
        git_bound.fetch('--all')

        origin = git_bound.remote('show').strip()
        active_ref = git_bound('symbolic-ref', 'HEAD').strip()
        tracking_ref = active_ref.replace(
            'heads', 'remotes/{0}'.format(origin)
        )

        hash_of_ref = lambda x: git_bound('show-ref', '--hash', x).strip()
        date_of_ref = lambda x: _datetime_of_commit(repository, x)
        hash_and_date = lambda x: (hash_of_ref(x), date_of_ref(x))

        active, active_date = hash_and_date(active_ref)
        tracking, tracking_date = hash_and_date(tracking_ref)

        is_different = active != tracking
        is_tracking_newer = tracking_date > active_date
    except (AttributeError, git.error, AssertionError):
        # The Python Git library issues some strange errors during
        # a fetch on occasion, so this "diaper"ish except is intended
        # to allow the process to continue without failing with a traceback.

        # Let the result be that new commits are available even though we had
        # an error. During a fetch this is typically the case.
        is_different = True
        is_tracking_newer = True

    return is_different and is_tracking_newer
