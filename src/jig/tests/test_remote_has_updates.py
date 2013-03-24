from tempfile import mkdtemp
from shutil import rmtree
from time import sleep

from git import Repo
from git.exc import GitCommandError
from mock import patch

from jig.tests.testcase import JigTestCase
from jig.gitutils import clone, remote_has_updates


class TestRemoteHasUpdates(JigTestCase):

    """
    Git utils check if the active branch is older than the remote.

    """
    def setUp(self):
        super(TestRemoteHasUpdates, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.remote_repo = repo
        self.remote_workingdir = working_dir

        self.local_workingdir = mkdtemp()

        clone(self.remote_workingdir, self.local_workingdir)

        self.local_repo = Repo(self.local_workingdir)

    def tearDown(self):
        rmtree(self.local_workingdir)

    def test_no_updates(self):
        """
        If the remote and local are the same, return False.
        """
        self.assertFalse(remote_has_updates(self.local_workingdir))

    def test_has_updates(self):
        """
        If the remote is newer than the local, returns True.
        """
        # Wait a second so the date is different than our original commit
        sleep(1.0)

        self.commit(self.remote_workingdir, 'a.txt', 'aaa')

        self.assertTrue(remote_has_updates(self.local_workingdir))

    def test_handles_git_python_exceptions(self):
        """
        If the fetch to retrieve new information results in an exception.
        """
        with patch('jig.gitutils.git') as git:
            git.Repo.side_effect = AttributeError

            self.assertTrue(remote_has_updates(self.local_workingdir))

        with patch('jig.gitutils.git') as git:
            git.Repo.side_effect = GitCommandError(None, None)

            self.assertTrue(remote_has_updates(self.local_workingdir))

        with patch('jig.gitutils.git') as git:
            git.Repo.side_effect = AssertionError

            self.assertTrue(remote_has_updates(self.local_workingdir))

    def test_has_updates_in_local(self):
        """
        If the updates are in the local branch, return False.
        """
        sleep(1.0)

        self.commit(self.local_workingdir, 'a.txt', 'aaa')

        self.assertFalse(remote_has_updates(self.local_workingdir))

    def test_remote_different_branch_has_updates(self):
        """
        If the remote has a non-"master" branch as the default.
        """
        # Create a new branch on the remote
        alternate = self.remote_repo.create_head('alternate')
        self.remote_repo.head.reference = alternate
        self.remote_repo.head.reset(index=True, working_tree=True)

        # Clone the remote branch locally
        self.local_workingdir = mkdtemp()
        clone(self.remote_workingdir, self.local_workingdir,
              branch='alternate')
        self.local_repo = Repo(self.local_workingdir)

        # If we check now, no new updates have been made
        self.assertFalse(remote_has_updates(self.local_workingdir))

        # Let the clock rollover
        sleep(1.0)

        # Commit to the 'alternate' branch on the remote
        self.commit(self.remote_workingdir, 'a.txt', 'aaa')

        self.assertTrue(remote_has_updates(self.local_workingdir))
