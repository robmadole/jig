# coding=utf-8
from tempfile import mkdtemp

from jig.tests.testcase import CommandTestCase, cd_gitrepo
from jig.exc import ForcedExit
from jig.commands import init


class TestInitCommand(CommandTestCase):

    """
    Test the init subcommand.

    """
    command = init.Command

    def test_initialize_repo(self):
        """
        We inititialize a repository with jig.
        """
        self.run_command(self.gitrepodir)

        self.assertEqual(
            u'Git repository has been initialized for use with Jig.\n',
            self.output)

    @cd_gitrepo
    def test_initialize_current_directory(self):
        """
        Defaults to the current directory and initializes.
        """
        # Leave the directory argument off, which should make the command
        # use the current working directory.
        self.run_command()

        self.assertEqual(
            u'Git repository has been initialized for use with Jig.\n',
            self.output)

    def test_handles_error(self):
        """
        Catches repository that do not exist.
        """
        with self.assertRaises(ForcedExit):
            self.run_command(mkdtemp())

        self.assertIn('is not a Git repository', self.error)
