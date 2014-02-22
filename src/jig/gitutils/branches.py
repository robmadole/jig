import git
from git.exc import GitCommandError, BadObject

from jig.exc import GitRevListFormatError, GitRevListMissing


def parse_rev_range(repository, rev_range):
    """
    Convert revision range to two :class:`git.objects.commit.Commit` objects.

    :param string repository: path to the Git repository
    :param string rev_range: Double dot-separated revision range, like
        "FOO..BAR"
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
