from os import unlink
from os.path import join, isfile
from contextlib import contextmanager
from functools import partial
from itertools import chain, combinations

from git import Repo
from git.objects.commit import Commit

from jig.tests.testcase import JigTestCase
from jig.exc import GitRevListMissing, GitRevListFormatError
from jig.gitutils.branches import (
    parse_rev_range, prepare_working_directory,
    _prepare_against_staged_index, _prepare_with_rev_range)


@contextmanager
def assert_git_status_unchanged(repository):
    """
    Make sure that the working directory remains in the same rough state.

    :param string repository: Git repo
    """
    before = Repo(repository).git.status('--long')

    yield

    after = Repo(repository).git.status('--long')

    assert before == after, "Working directory status has changed"


class TestParseRevRange(JigTestCase):

    """
    Git utils revision range parser.

    """
    def setUp(self):
        super(TestParseRevRange, self).setUp()

        self.gitrepo, self.gitrepodir, _ = self.repo_from_fixture('repo01')

    def assertIsRevRange(self, rev_range):
        commit_a, commit_b = rev_range

        self.assertIsInstance(commit_a, Commit)
        self.assertIsInstance(commit_b, Commit)

    def test_bad_format(self):
        """
        If the revision range doesn't match the expected format.
        """
        with self.assertRaises(GitRevListFormatError):
            parse_rev_range(self.gitrepodir, 'A-B')

    def test_bad_format_missing_rev(self):
        """
        If the format is correct but the revisions are missing.
        """
        with self.assertRaises(GitRevListFormatError):
            parse_rev_range(self.gitrepodir, '..B')

        with self.assertRaises(GitRevListFormatError):
            parse_rev_range(self.gitrepodir, 'A..')

    def test_bad_revs(self):
        """
        If the format is good but the revisions do not exist.
        """
        with self.assertRaises(GitRevListMissing):
            parse_rev_range(self.gitrepodir, 'FOO..BAR')

    def test_good_revs(self):
        """
        The revisions to exist.
        """
        self.assertIsRevRange(parse_rev_range(self.gitrepodir, 'HEAD^1..HEAD'))

    def test_local_branch(self):
        """
        A branch that is newly created can be referenced.
        """
        self.gitrepo.create_head('feature-branch')

        self.assertIsRevRange(
            parse_rev_range(self.gitrepodir, 'HEAD^1..feature-branch')
        )

    def test_out_of_range(self):
        """
        A revision is out of range.
        """
        with self.assertRaises(GitRevListMissing):
            parse_rev_range(self.gitrepodir, 'HEAD~1000..HEAD')


class TestPrepareAgainstStagedIndex(JigTestCase):

    """
    Prepare the working directory against the staged index.

    """
    def setUp(self):
        self.reset_gitrepo()

    def reset_gitrepo(self):
        del self.gitrepodir

        self.commit(self.gitrepodir, 'a.txt', 'a'),
        self.commit(self.gitrepodir, 'b.txt', 'b'),
        self.commit(self.gitrepodir, 'c.txt', 'c'),
        self.commit(self.gitrepodir, 'd.txt', 'd')

    @property
    def repo(self):
        return Repo(self.gitrepodir)

    def diff_head(self):
        return self.repo.index.diff('HEAD')

    @contextmanager
    def prepare(self):
        with assert_git_status_unchanged(self.gitrepodir):
            with _prepare_against_staged_index(self.repo) as stash:
                yield stash

    def test_working_directory_clean(self):
        """
        Working directory is clean.
        """
        with self.prepare() as stash:
            self.assertIsNone(stash)

    def test_untracked(self):
        """
        Untracked file present.
        """
        self.create_file(self.gitrepodir, 'e.txt', 'e')

        expected_untracked = self.repo.untracked_files

        with self.prepare() as stash:
            self.assertIsNone(stash)

            # We have no untracked files, they are stashed
            self.assertEqual(expected_untracked, self.repo.untracked_files)

    def test_staged(self):
        """
        Staged file.
        """
        self.stage(self.gitrepodir, 'a.txt', 'aa')

        before = self.diff_head()

        with self.prepare() as stash:
            self.assertIsNone(stash)

            # The staged changes are not stashed
            self.assertEqual(before, self.diff_head())

    def test_modified(self):
        """
        Modified file.
        """
        self.modify_file(self.gitrepodir, 'a.txt', 'aa')

        with self.prepare() as stash:
            self.assertIsNotNone(stash)

            # The modifications are stashed
            self.assertEqual([], self.repo.index.diff(None))

    def test_stageremoved(self):
        """
        Staged removal of a file.
        """
        self.stage_remove(self.gitrepodir, 'a.txt')

        with self.prepare() as stash:
            self.assertIsNone(stash)

    def test_fsremoved(self):
        """
        Non-staged removal of a file.
        """
        unlink(join(self.gitrepodir, 'a.txt'))

        with self.prepare() as stash:
            self.assertIsNotNone(stash)

            # The file is temporarily restored
            self.assertTrue(isfile(join(self.gitrepodir, 'a.txt')))

    def test_combinations(self):
        """
        Combine all variations of modification, creation, or removal.
        """
        def modified():
            self.modify_file(self.gitrepodir, 'a.txt', 'aa')
        modified.should_stash = True

        def staged():
            self.stage(self.gitrepodir, 'b.txt', 'bb')
        staged.should_stash = False

        def indexremoved():
            self.stage_remove(self.gitrepodir, 'c.txt')
        indexremoved.should_stash = False

        def fsremoved():
            unlink(join(self.gitrepodir, 'd.txt'))
        fsremoved.should_stash = True

        def untracked():
            self.create_file(self.gitrepodir, 'e.txt', 'e')
        untracked.should_stash = False

        mutation = partial(
            combinations,
            (modified, staged, indexremoved, fsremoved, untracked)
        )

        options = chain.from_iterable(map(mutation, [2, 3, 4, 5]))

        for option in options:
            # Mutate the Git repository
            map(lambda x: x(), option)

            with self.prepare() as stash:
                should_stash = any(map(lambda x: x.should_stash, option))

                if should_stash:
                    self.assertIsNotNone(stash)
                else:
                    self.assertIsNone(stash)

            self.reset_gitrepo()


class TestPrepareWorkingDirectory(JigTestCase):

    """

    """
    def test_working_directory_clean_no_rev_range(self):
        """
        Working directory is clean and no revision range is passed.
        """
        with prepare_working_directory(self.gitrepodir) as stash:
            self.assertIsNone(stash)
