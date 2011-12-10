# coding=utf-8
from tempfile import mkdtemp

from becareful.tests.testcase import CommandTestCase, PluginTestCase
from becareful.exc import ForcedExit
from becareful.plugins import set_bcconfig
from becareful.commands import init, runnow


class TestInitCommand(CommandTestCase):

    """
    Test the init subcommand.

    """
    command = init.Command

    def test_initialize_repo(self):
        """
        We inititialize a repository with BeCareful.
        """
        self.run_command(self.gitrepodir)

        self.assertEqual(
            u'Git repository has been initialized for use with BeCareful\n',
            self.output)

    def test_handles_error(self):
        """
        Catches repository that do not exist.
        """
        with self.assertRaises(ForcedExit) as ec:
            self.run_command(mkdtemp())

        self.assertIn('is not a Git repository', self.error)


class TestRunNowCommand(CommandTestCase, PluginTestCase):

    """
    Test the runnow command.

    """
    command = runnow.Command

    def test_no_changes(self):
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        self.run_command(self.gitrepodir)

    def test_changes(self):
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        self.run_command(self.gitrepodir)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: b.txt
                b is +

            Ran 1 plugin
                Info 0 Warn 1 Stop 0
            """, self.output)

    def test_handles_error(self):
        with self.assertRaises(ForcedExit):
            self.run_command(mkdtemp())

        self.assertIn(u'This repository has not been initialized. Run '
            'becareful init GITREPO to set it up\n', self.error)
