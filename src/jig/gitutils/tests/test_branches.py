from git.objects.commit import Commit

from jig.tests.testcase import JigTestCase
from jig.exc import GitRevListMissing, GitRevListFormatError
from jig.gitutils.branches import parse_rev_range


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

        self.assertIsRevRange(parse_rev_range(self.gitrepodir, 'HEAD^1..feature-branch'))

    def test_out_of_range(self):
        """
        A revision is out of range.
        """
        with self.assertRaises(GitRevListMissing):
            parse_rev_range(self.gitrepodir, 'HEAD~1000..HEAD')
