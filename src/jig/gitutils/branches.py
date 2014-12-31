from os import unlink
from tempfile import mkstemp
from contextlib import contextmanager
from collections import namedtuple

import sh

from jig.exc import (
    GitRevListFormatError, GitRevListMissing, GitWorkingDirectoryDirty,
    TrackingBranchMissing)
from jig.gitutils.commands import git
from jig.gitutils.checks import repo_is_dirty


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
        commit_a = git(repository)('rev-parse', rev_a).strip()
        commit_b = git(repository)('rev-parse', rev_b).strip()

        return RevRangePair(commit_a, commit_b, rev_range)
    except sh.ErrorReturnCode:
        raise GitRevListMissing(rev_range)


@contextmanager
def _prepare_with_rev_range(repo, rev_range):
    # If a rev_range is specified then we need to make sure the working
    # directory is completely clean before continuing.
    if rev_range and repo_is_dirty(repo):
        raise GitWorkingDirectoryDirty()

    git_bound = git(repo)

    try:
        head = git_bound('symbolic-ref', '--short', 'HEAD').strip()
    except git.error:
        head = git_bound('rev-parse', 'HEAD').strip()

    git_bound.checkout(rev_range.b)

    try:
        yield head
    finally:
        git_bound.checkout(head)


@contextmanager
def _prepare_against_staged_index(repo):
    """
    Prepare the working directory to run Jig off the staged index.

    :param git.Repo repo: Git repo
    """
    stash = None
    git_bound = git(repo)

    check_kwargs = {
        'index': False,
        'working_directory': True,
        'untracked_files': False
    }

    if repo_is_dirty(repo, **check_kwargs):
        stash = git_bound.stash('save', '--keep-index')

    try:
        yield stash
    finally:
        if not stash:
            return

        os_handle, patchfile = mkstemp()

        git_bound.diff(
            '--color=never', '-R', 'stash@{0}',
            _out=patchfile)

        git_bound.apply(patchfile)

        unlink(patchfile)

        git_bound.stash('drop', '-q')


@contextmanager
def prepare_working_directory(gitrepo, rev_range=None):
    """
    Use Git stash and checkout to prepare the working directory for a Jig run.

    :param string gitrepo: file path to the Git repository
    :param RevRangePair rev_range:
    """
    if rev_range:
        with _prepare_with_rev_range(gitrepo, rev_range) as head:
            yield head
    else:
        with _prepare_against_staged_index(gitrepo) as stash:
            yield stash


RevRangePair = namedtuple('RevRangePair', 'a b raw')


class Tracked(object):

    """
    Manage the tracking branch Jig uses when running in CI mode.

    """
    def __init__(self, gitrepo, tracking_branch='jig-ci-last-run'):
        self.gitrepo = gitrepo
        self.tracking_branch = tracking_branch
        self.git = git(path=self.gitrepo)

    @property
    def _full_tracking_ref(self):
        return 'refs/heads/{0}'.format(self.tracking_branch)

    @property
    def exists(self):
        """
        Whether the tracking branch exists in the Git repository.
        """
        try:
            self.git('rev-parse', self._full_tracking_ref)

            return True
        except git.error:
            return False

    def _update_ref(self, ref):
        """
        Updates the Git ref for the tracking branch to a new value.
        """
        rev = self.git('rev-parse', ref).strip()

        self.git('update-ref', self._full_tracking_ref, rev)

        return rev

    def _create(self):
        """
        Create a new head on the repository with the tracking branch name.
        """
        return self._update_ref('HEAD')

    @property
    def rev(self):
        """
        The commit representing the tracking branch.
        """
        if not self.exists:
            raise TrackingBranchMissing(self.tracking_branch)

        return self.git('rev-parse', self._full_tracking_ref).strip()

    def update(self, ref='HEAD'):
        """
        Change the tracking branch to a new commit.
        """
        if not self.exists:
            self._update_ref('HEAD')

        return self._update_ref(ref)
