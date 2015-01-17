from os.path import join
from tempfile import mkdtemp
from shutil import rmtree
from time import sleep

from mock import patch

from jig.tests.testcase import JigTestCase
from jig.exc import GitCloneError
from jig.packages.sh import sh
from jig.gitutils.commands import git
from jig.gitutils.checks import is_git_repo
from jig.gitutils.remote import clone, remote_has_updates


class TestClone(JigTestCase):

    """
    Git utils clone method can clone a repository.

    """
    def setUp(self):
        self.workingdir = mkdtemp()

    def tearDown(self):
        rmtree(self.workingdir)

    def test_clone_valid_repo(self):
        """
        Valid repo can be cloned.
        """
        with patch('jig.gitutils.remote.git') as mock_git:
            to_dir = join(self.workingdir, 'a')

            result = clone('http://github.com/user/repo', to_dir)

            mock_git.return_value.assert_called_with(
                'clone', 'http://github.com/user/repo', to_dir
            )

        self.assertTrue(result)

    def test_clone_invalid_repo(self):
        """
        Invalid repo raises error.
        """
        with patch('jig.gitutils.remote.git') as mock_git:
            mock_git.side_effect = sh.ErrorReturnCode(
                'git clone', '', 'error'
            )
            mock_git.error = sh.ErrorReturnCode

            to_dir = join(self.workingdir, 'a')

            with self.assertRaises(GitCloneError) as gce:
                clone('http://github.com/user/repo', to_dir)   # pragma: no branch

            self.assertEqual(
                'error',
                str(gce.exception)
            )

    def test_local_directory_clone(self):
        """
        Clones a local file-based Git repository.
        """
        to_dir = join(self.workingdir, 'a')

        clone(self.gitrepodir, to_dir)

        self.assertTrue(is_git_repo(to_dir))

    def test_clone_branch(self):
        """
        Clone a specific branch of a repository.
        """
        with patch('jig.gitutils.remote.git') as mock_git:
            to_dir = join(self.workingdir, 'a')

            clone(
                'http://github.com/user/repo',
                to_dir,
                branch='alternate'
            )

            mock_git.return_value.assert_called_with(
                'clone', '--branch', 'alternate',
                'http://github.com/user/repo', to_dir
            )


class TestRemoteHasUpdates(JigTestCase):

    """
    Git utils check if the active branch is older than the remote.

    """
    def setUp(self):
        super(TestRemoteHasUpdates, self).setUp()

        self.remote_repo, diffs = self.repo_from_fixture('repo01')

        self.local_repo = mkdtemp()

        clone(self.remote_repo, self.local_repo)

    def tearDown(self):
        rmtree(self.local_repo)

    def test_no_updates(self):
        """
        If the remote and local are the same, return False.
        """
        self.assertFalse(remote_has_updates(self.local_repo))

    def test_has_updates(self):
        """
        If the remote is newer than the local, returns True.
        """
        # Wait a second so the date is different than our original commit
        sleep(1.0)

        self.commit(self.remote_repo, 'a.txt', 'aaa')

        self.assertTrue(remote_has_updates(self.local_repo))

    def test_handles_git_python_exceptions(self):
        """
        If the fetch to retrieve new information results in an exception.
        """
        with patch('jig.gitutils.remote.git') as git:
            git.error = sh.ErrorReturnCode

            git.side_effect = AttributeError

            self.assertTrue(remote_has_updates(self.local_repo))

        with patch('jig.gitutils.remote.git') as git:
            git.error = sh.ErrorReturnCode

            git.side_effect = git.error('', '', '')

            self.assertTrue(remote_has_updates(self.local_repo))

        with patch('jig.gitutils.remote.git') as git:
            git.error = sh.ErrorReturnCode

            git.side_effect = AssertionError

            self.assertTrue(remote_has_updates(self.local_repo))

    def test_has_updates_in_local(self):
        """
        If the updates are in the local branch, return False.
        """
        sleep(1.0)

        self.commit(self.local_repo, 'a.txt', 'aaa')

        self.assertFalse(remote_has_updates(self.local_repo))

    def test_remote_different_branch_has_updates(self):
        """
        If the remote has a non-"master" branch as the default.
        """
        # Create a new branch on the remote
        git(self.remote_repo)('checkout', '-b', 'alternate')

        # Clone the remote branch locally
        self.local_repo = mkdtemp()
        clone(self.remote_repo, self.local_repo,
              branch='alternate')

        # If we check now, no new updates have been made
        self.assertFalse(remote_has_updates(self.local_repo))

        # Let the clock rollover
        sleep(1.0)

        # Commit to the 'alternate' branch on the remote
        self.commit(self.remote_repo, 'a.txt', 'aaa')

        self.assertTrue(remote_has_updates(self.local_repo))
