from os import unlink
from os.path import join, isfile
from contextlib import contextmanager
from functools import partial
from itertools import chain, combinations

from mock import patch, MagicMock

from jig.tests.testcase import JigTestCase
from jig.exc import (
    GitRevListMissing, GitRevListFormatError, GitWorkingDirectoryDirty,
    TrackingBranchMissing)
from jig.gitutils.commands import git
from jig.gitutils.branches import (
    parse_rev_range, prepare_working_directory,
    _prepare_against_staged_index, _prepare_with_rev_range, Tracked)


@contextmanager
def assert_git_status_unchanged(repository):
    """
    Make sure that the working directory remains in the same rough state.

    :param string repository: Git repo
    """
    def long_status(repository):
        output = git(repository).status('--long')

        # Skip the first line, it tells us the branch
        return output.splitlines()[1:]

    before = long_status(repository)

    yield

    after = long_status(repository)

    assert before == after, "Working directory status has changed"


class PrepareTestCase(JigTestCase):

    """
    Base test class for private functions that prepare the working directory.

    """
    def setUp(self):
        super(PrepareTestCase, self).setUp()

        self.reset_gitrepo()

    def reset_gitrepo(self):
        del self.gitrepodir

        self.commits = [
            self.commit(self.gitrepodir, 'a.txt', 'a'),
            self.commit(self.gitrepodir, 'b.txt', 'b'),
            self.commit(self.gitrepodir, 'c.txt', 'c'),
            self.commit(self.gitrepodir, 'd.txt', 'd')
        ]

    def diff_head(self):
        return git(self.gitrepodir).diff()

    @contextmanager
    def prepare(self):
        with assert_git_status_unchanged(self.gitrepodir):
            with self.prepare_context_manager() as subject:
                yield subject


class TestParseRevRange(JigTestCase):

    """
    Git utils revision range parser.

    """
    def setUp(self):
        super(TestParseRevRange, self).setUp()

        self.gitrepodir, _ = self.repo_from_fixture('repo01')

    def assertIsRevRange(self, rev_range):
        self.assertEqual(len(rev_range.a), 40)
        self.assertEqual(len(rev_range.b), 40)

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
        git(self.gitrepodir).branch('feature-branch')

        self.assertIsRevRange(
            parse_rev_range(self.gitrepodir, 'HEAD^1..feature-branch')
        )

    def test_out_of_range(self):
        """
        A revision is out of range.
        """
        with self.assertRaises(GitRevListMissing):
            parse_rev_range(self.gitrepodir, 'HEAD~1000..HEAD')


class TestPrepareAgainstStagedIndex(PrepareTestCase):

    """
    Prepare the working directory against the staged index.

    """
    def prepare_context_manager(self):
        return _prepare_against_staged_index(self.gitrepodir)

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

        ls_files = ('ls-files', '--other')
        untracked = lambda: git(self.gitrepodir)(*ls_files).splitlines()

        expected_untracked = untracked()

        with self.prepare() as stash:
            self.assertIsNone(stash)

            # We have no untracked files, they are stashed
            self.assertEqual(expected_untracked, untracked())

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
            self.assertFalse(git(self.gitrepodir).diff().strip())

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


class TestPrepareWithRevRange(PrepareTestCase):

    """
    With a given rev range test that we can checkout the repository.

    """
    def prepare_context_manager(self):
        rev_range_parsed = parse_rev_range(
            self.gitrepodir,
            self.rev_range
        )

        return _prepare_with_rev_range(self.gitrepodir, rev_range_parsed)

    def test_dirty_working_directory(self):
        """
        Dirty working directory will raise an exception.
        """
        self.rev_range = 'HEAD~3..HEAD~0'

        # Force the working directory to be dirty
        self.modify_file(self.gitrepodir, 'a.txt', 'aa')

        with self.assertRaises(GitWorkingDirectoryDirty):
            self.prepare().__enter__()

    def test_yields_git_named_head(self):
        """
        The object that is yielded is a short ref.
        """
        self.rev_range = 'HEAD~1..HEAD~0'

        with self.prepare() as head:
            self.assertEqual('master', head)

    def test_yields_git_detached_head(self):
        """
        If detached HEAD, object that is yielded is a hash.
        """
        self.rev_range = 'HEAD~1..HEAD~0'

        # Detach the head by checking out the commit hash
        git(self.gitrepodir).checkout(self.commits[-1])

        with self.prepare() as head:
            self.assertIsGitSha1(head)

    def test_detached_head_right_side_of_rev_range(self):
        """
        The head object points to the right side of the rev range.
        """
        self.rev_range = 'HEAD~2..HEAD~1'

        # HEAD~1 is going to be our second to last commit
        expected = self.commits[-2]

        with self.prepare():
            # The symbolic ref for HEAD should now be our expected commit
            self.assertEqual(
                git(self.gitrepodir)('rev-parse', 'HEAD').strip(),
                expected
            )

    def test_returns_to_master(self):
        """
        After exiting the context manager, we should be back on master.
        """
        self.rev_range = 'HEAD~2..HEAD~1'

        with self.prepare():
            pass

        self.assertEqual(
            git(self.gitrepodir)('symbolic-ref', 'HEAD').strip(),
            'refs/heads/master'
        )

    def test_returns_to_detached_head(self):
        """
        From a detached head upon exiting we should be back where we started.
        """
        self.rev_range = 'HEAD~2..HEAD~1'

        # Detach the head by checking out the commit hash
        git(self.gitrepodir).checkout(self.commits[-2])

        # HEAD~1 is going to be our third to last commit
        expected = self.commits[-3]

        head = lambda: git(self.gitrepodir)('rev-parse', 'HEAD').strip()

        with self.prepare():
            self.assertEqual(
                head(),
                expected
            )

        # And we are back to our detached head we started with
        self.assertEqual(
            head(),
            self.commits[-2]
        )


class TestPrepareWorkingDirectory(JigTestCase):

    """
    Make the working directory suitable for running Jig.

    """
    def setUp(self):
        super(TestPrepareWorkingDirectory, self).setUp()

        self.gitrepodir, _ = self.repo_from_fixture('repo01')

    def test_no_rev_range(self):
        """
        Should prepare against the staged index if no rev range.
        """
        prepare_function = \
            'jig.gitutils.branches._prepare_against_staged_index'

        with patch(prepare_function) as p:
            p.return_value = MagicMock()

            with prepare_working_directory(self.gitrepodir):
                pass

        self.assertTrue(p.return_value.__enter__.called)

    def test_rev_range(self):
        """
        Should checkout the Git repo at the end of the rev range.
        """
        prepare_function = \
            'jig.gitutils.branches._prepare_with_rev_range'

        with patch(prepare_function) as p:
            p.return_value = MagicMock()

            rev_range_parsed = parse_rev_range(
                self.gitrepodir, 'HEAD~1..HEAD~0'
            )

            with prepare_working_directory(self.gitrepodir, rev_range_parsed):
                pass

        self.assertTrue(p.return_value.__enter__.called)


class TestTracked(JigTestCase):

    """
    Git repositories can be tracked for CI mode.

    """
    def setUp(self):
        super(TestTracked, self).setUp()

        self.commits = [
            self.commit(self.gitrepodir, 'a.txt', 'a'),
            self.commit(self.gitrepodir, 'b.txt', 'b'),
            self.commit(self.gitrepodir, 'c.txt', 'c'),
        ]

    def create_tracking_branch(self, name='jig-ci-last-run', rev='HEAD'):
        """
        Creates the tracking branch with a reference to the given rev.
        """
        rev_parsed = git(self.gitrepodir)('rev-parse', rev).strip()

        git(self.gitrepodir)(
            'update-ref',
            'refs/heads/{0}'.format(name),
            rev_parsed
        )

    def test_tracking_branch_does_not_exist(self):
        """
        Tracking branch does not exist.
        """
        tracked = Tracked(self.gitrepodir)

        self.assertFalse(tracked.exists)

    def test_tracking_branch_exists(self):
        """
        Tracking branch exists.
        """
        self.create_tracking_branch()

        tracked = Tracked(self.gitrepodir)

        self.assertTrue(tracked.exists)

    def test_tracking_branch_by_a_different_name(self):
        """
        Can check existence by a different name than the default.
        """
        name = 'different-tracking-name'

        self.create_tracking_branch(name=name)

        tracked = Tracked(self.gitrepodir, name)

        self.assertTrue(tracked.exists)

    def test_update_defaults_to_head(self):
        """
        Updating the tracking branch defaults to current HEAD.
        """
        tracked = Tracked(self.gitrepodir)

        rev = tracked.update()

        self.assertEqual(
            rev,
            self.commits[-1]
        )

    def test_non_existent_reference(self):
        """
        Without a tracking branch trying to get a references to it raises.
        """
        tracked = Tracked(self.gitrepodir)

        with self.assertRaises(TrackingBranchMissing):
            tracked.rev

    def test_tracking_branch_reference(self):
        """
        With a tracking branch we can get a reference to it.
        """
        self.create_tracking_branch(rev='HEAD~2')

        tracked = Tracked(self.gitrepodir)

        self.assertEqual(
            tracked.rev,
            self.commits[0]
        )

    def test_update_takes_commit_hash(self):
        """
        Updating the tracking branch can be done with a commit hash.
        """
        tracked = Tracked(self.gitrepodir)

        tracked.update(self.commits[0])

        self.assertEqual(
            tracked.rev,
            self.commits[0]
        )

    def test_update_moves_head_forward(self):
        """
        The tracking branch reference can be moved forward.
        """
        self.create_tracking_branch(rev='HEAD~2')

        tracked = Tracked(self.gitrepodir)

        tracked.update()

        self.assertEqual(
            tracked.rev,
            self.commits[-1]
        )
