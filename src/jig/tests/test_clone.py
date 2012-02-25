from os.path import join
from tempfile import mkdtemp
from shutil import rmtree

from mock import patch
from git import Git, GitCommandError

from jig.tests.testcase import JigTestCase
from jig.exc import GitCloneError
from jig.gitutils import clone, is_git_repo


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
        with patch.object(Git, 'execute'):
            to_dir = join(self.workingdir, 'a')

            Git.execute.return_value = 'Cloning into X'

            gitobj = clone('http://github.com/user/repo', to_dir)

            Git.execute.assert_called_with(['git', 'clone',
                'http://github.com/user/repo', to_dir])

        self.assertIsInstance(gitobj, Git)

    def test_clone_invalid_repo(self):
        """
        Invalid repo raises error.
        """
        with patch.object(Git, 'execute'):
            to_dir = join(self.workingdir, 'a')

            Git.execute.side_effect = GitCommandError(['command'], 128,
                stderr='bad command')

            with self.assertRaises(GitCloneError) as gce:
                clone('http://github.com/user/repo', to_dir)

            self.assertIn("'command' returned exit status 128: bad command",
                gce.exception)

    def test_local_directory_clone(self):
        """
        Clones a local file-based Git repository.
        """
        to_dir = join(self.workingdir, 'a')

        clone(self.gitrepodir, to_dir)

        self.assertTrue(is_git_repo(to_dir))
