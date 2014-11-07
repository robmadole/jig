from os import unlink
from tempfile import mkstemp
from functools import partial
from contextlib import contextmanager
from collections import namedtuple

from jig.exc import (
    GitRevListFormatError, GitRevListMissing, GitWorkingDirectoryDirty,
    TrackingBranchMissing)
from jig.gitutils.checks import working_directory_dirty


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

        return RevRangePair(commit_a, commit_b, rev_range)
    except (BadObject, GitCommandError):
        raise GitRevListMissing(rev_range)


@contextmanager
def _prepare_with_rev_range(repo, rev_range):
    # If a rev_range is specified then we need to make sure the working
    # directory is completely clean before continuing.
    if rev_range and working_directory_dirty(repo.working_dir):
        raise GitWorkingDirectoryDirty()

    try:
        head = repo.head.reference
        return_to_normal = head.checkout
    except TypeError:
        head = repo.head.commit
        return_to_normal = partial(repo.git.checkout, head.hexsha)

    repo.git.checkout(rev_range.b.hexsha)

    try:
        yield head
    finally:
        return_to_normal()


@contextmanager
def _prepare_against_staged_index(repo):
    """
    Prepare the working directory to run Jig off the staged index.

    :param git.Repo repo: Git repo
    """
    stash = None

    if repo.is_dirty(index=False, working_tree=True, untracked_files=False):
        stash = repo.git.stash('save', '--keep-index')

    try:
        yield stash
    finally:
        if not stash:
            return

        os_handle, patchfile = mkstemp()

        with open(patchfile, 'w') as fh:
            repo.git.diff(
                '--color=never', '-R', 'stash@{0}',
                output_stream=fh)

        repo.git.apply(patchfile)

        unlink(patchfile)

        repo.git.stash('drop', '-q')


@contextmanager
def prepare_working_directory(repository, rev_range=None):
    """
    Use Git stash and checkout to prepare the working directory for a Jig run.

    :param string gitrepo: file path to the Git repository
    :param RevRangePair rev_range:
    """
    repo = git.Repo(repository)

    if rev_range:
        with _prepare_with_rev_range(repo, rev_range) as head:
            yield head
    else:
        with _prepare_against_staged_index(repo) as stash:
            yield stash


RevRangePair = namedtuple('RevRangePair', 'a b raw')


class Tracked(object):

    """
    Manage the tracking branch Jig uses when running in CI mode.

    """
    def __init__(self, gitrepo, tracking_branch='jig-ci-last-run'):
        self.gitrepo = git.Repo(gitrepo)
        self.tracking_branch = tracking_branch

    @property
    def exists(self):
        """
        Whether the tracking branch exists in the Git repository.
        """
        return self.tracking_branch in self.gitrepo.references

    def _create(self):
        """
        Create a new head on the repository with the tracking branch name.
        """
        return self.gitrepo.create_head(self.tracking_branch)

    @property
    def reference(self):
        """
        The :py:class:`git.Commit` object representing the tracking branch.
        """
        if not self.exists:
            raise TrackingBranchMissing(self.tracking_branch)

        return self.gitrepo.references[self.tracking_branch]

    def update(self, commit='HEAD'):
        """
        Change the tracking branch to a new commit.
        """
        reference = self.reference if self.exists else self._create()

        reference.commit = commit

        return reference
