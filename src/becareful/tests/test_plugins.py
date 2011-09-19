from os import rmdir
from tempfile import mkdtemp

from becareful.tests.testcase import BeCarefulTestCase
from becareful.exc import NotGitRepo, AlreadyInitialized
from becareful.plugins import initializer


class TestPlugins(BeCarefulTestCase):

    """
    Work with plugins.

    """
    def test_not_git_repo(self):
        """
        Refuses to initialize a non-Git repo.
        """
        badrepo = mkdtemp()

        try:
            with self.assertRaises(NotGitRepo) as c:
                initializer(badrepo)
        finally:
            rmdir(badrepo)

    def test_already_initialized(self):
        # Initialize it once
        initializer(self.gitrepodir)

        with self.assertRaises(AlreadyInitialized) as c:
            # Initialize the same directory again
            initializer(self.gitrepodir)
