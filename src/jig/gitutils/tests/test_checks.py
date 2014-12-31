from tempfile import mkdtemp

from jig.tests.testcase import JigTestCase
from jig.plugins import initializer
from jig.gitutils.commands import git
from jig.gitutils.checks import (
    is_git_repo, repo_jiginitialized, repo_is_dirty)


class TestIsGitRepo(JigTestCase):

    """
    Detect if a directory is a Git repository or not.

    """
    def test_is_not_git_directory(self):
        """
        Detects a non-git initialized directory.
        """
        self.assertFalse(is_git_repo(mkdtemp()))

    def test_is_git_directory(self):
        """
        Detects a directory that has been initialized for Git.
        """
        directory = mkdtemp()

        git(directory).init('.')

        self.assertTrue(is_git_repo(directory))


class TestRepoJiginitialized(JigTestCase):

    """
    Detect Jig-initialized repositories.

    """
    def test_is_not_jig_initialized_directory(self):
        """
        Detect the directory has not been initialized.
        """
        self.assertFalse(repo_jiginitialized(mkdtemp()))

    def test_is_jig_initialized_directory(self):
        """
        Detect the directory has been initialized.
        """
        directory = mkdtemp()

        git(directory).init('.')

        initializer(directory)

        self.assertTrue(repo_jiginitialized(directory))


class TestRepoIsDirty(JigTestCase):

    """
    Detect dirty repositories.

    """
    def setUp(self):
        super(TestRepoIsDirty, self).setUp()

        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.commit(self.gitrepodir, 'b.txt', 'b')
        self.commit(self.gitrepodir, 'c.txt', 'c')

    def test_clean(self):
        """
        No changes have been made.
        """
        self.assertFalse(repo_is_dirty(self.gitrepodir))

    def test_has_staged_file(self):
        """
        Staged file in the index.
        """
        self.stage(self.gitrepodir, 'a.txt', 'aaa')

        self.assertTrue(repo_is_dirty(self.gitrepodir))

    def test_dirty_modified_file(self):
        """
        An existing file is modified.
        """
        self.modify_file(self.gitrepodir, 'a.txt', 'aaa')

        self.assertTrue(repo_is_dirty(self.gitrepodir))

    def test_clean_untracked_file(self):
        """
        An untracked file is not dirty by default.
        """
        self.create_file(self.gitrepodir, 'd.txt', 'd')

        self.assertFalse(repo_is_dirty(self.gitrepodir))

    def test_dirty_untracked_file(self):
        """
        An untracked file is not dirty by default.
        """
        self.create_file(self.gitrepodir, 'd.txt', 'd')

        self.assertTrue(repo_is_dirty(self.gitrepodir, untracked_files=True))

    def test_clean_through_disabling_everything(self):
        """
        Called with all False values it's clean.
        """
        self.stage(self.gitrepodir, 'a.txt', 'aaa')
        self.modify_file(self.gitrepodir, 'b.txt', 'bbb')
        self.create_file(self.gitrepodir, 'd.txt', 'd')

        self.assertFalse(
            repo_is_dirty(
                self.gitrepodir,
                index=False,
                working_directory=False,
                untracked_files=False
            )
        )
