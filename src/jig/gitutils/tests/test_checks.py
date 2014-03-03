from tempfile import mkdtemp

from git import Repo

from jig.tests.testcase import JigTestCase
from jig.plugins import initializer
from jig.gitutils.checks import (
    is_git_repo, repo_jiginitialized, working_directory_dirty)


class TestIsGitRepo(JigTestCase):

    """
    Detect if a directory is a Git repository or not.

    """
    def test_is_not_git_directory(self):
        self.assertFalse(is_git_repo(mkdtemp()))

    def test_is_git_directory(self):
        directory = mkdtemp()

        Repo.init(directory)

        self.assertTrue(is_git_repo(directory))


class TestRepoJiginitialized(JigTestCase):

    """
    Detect Jig-initialized repositories.

    """
    def test_is_not_jig_initialized_directory(self):
        self.assertFalse(repo_jiginitialized(mkdtemp()))

    def test_is_jig_initialized_directory(self):
        directory = mkdtemp()

        Repo.init(directory)

        initializer(directory)

        self.assertTrue(repo_jiginitialized(directory))


class TestWorkingDirctoryDirty(JigTestCase):

    """
    Detect clean and dirty working directories.

    """
    def setUp(self):
        super(TestWorkingDirctoryDirty, self).setUp()

        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.commit(self.gitrepodir, 'b.txt', 'b')
        self.commit(self.gitrepodir, 'c.txt', 'c')

    def test_directory_is_clean(self):
        """
        Working directory is clean.
        """
        self.assertFalse(working_directory_dirty(self.gitrepodir))

    def test_directory_has_modified_file(self):
        """
        An existing file is modified.
        """
        self.modify_file(self.gitrepodir, 'a.txt', 'aaa')

        self.assertTrue(working_directory_dirty(self.gitrepodir))

    def test_directory_has_untracked_file(self):
        """
        An untracked file is seen as dirty.
        """
        self.create_file(self.gitrepodir, 'd.txt', 'd')

        self.assertTrue(working_directory_dirty(self.gitrepodir))
