# coding=utf-8
from tempfile import mkdtemp
from contextlib import nested

from mock import patch

from jig.tests.testcase import (
    CommandTestCase, PluginTestCase, result_with_hint)
from jig.plugins import set_jigconfig
from jig.exc import ForcedExit
from jig.formatters.fancy import ATTENTION
from jig.commands import runnow
from jig.commands.hints import GIT_REPO_NOT_INITIALIZED


class TestRunNowCommand(CommandTestCase, PluginTestCase):

    """
    Test the runnow command.

    """
    command = runnow.Command

    def test_no_changes(self):
        """
        No changes have been made to the Git repository.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create the first commit
        self.commit(self.gitrepodir, 'a.txt', 'a')

        with self.assertRaises(SystemExit) as ec:
            self.run_command(self.gitrepodir)

        self.assertSystemExitCode(ec.exception, 0)

        self.assertEqual(
            u'No changes available for Jig to check, skipping.\n',
            self.output)

    def test_changes(self):
        """
        Changes are made and the plugin runs and gives us output.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.sys'),
            self.assertRaises(SystemExit)
        ) as (r_sys, ec):
            # Raise the error to halt execution like the real sys.exit would
            r_sys.exit.side_effect = SystemExit

            self.run_command(self.gitrepodir)

        r_sys.exit.assert_called_once_with(0)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: b.txt
                b is +

            {0}  Jig ran 1 plugin
                Info 0 Warn 1 Stop 0
            """.format(ATTENTION), self.output)

    def test_specific_plugin_installed(self):
        """
        A specific plugin can be ran if it's installed.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.sys'),
            self.assertRaises(SystemExit)
        ) as (r_sys, ec):
            # Raise the error to halt execution like the real sys.exit would
            r_sys.exit.side_effect = SystemExit

            self.run_command('--plugin plugin01 {0}'.format(self.gitrepodir))

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: b.txt
                b is +

            {0}  Jig ran 1 plugin
                Info 0 Warn 1 Stop 0
            """.format(ATTENTION), self.output)

    def test_specific_plugin_not_installed(self):
        """
        A specific plugin can be ran but it's not installed.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.sys'),
            self.assertRaises(SystemExit)
        ) as (r_sys, ec):
            # Raise the error to halt execution like the real sys.exit would
            r_sys.exit.side_effect = SystemExit

            self.run_command(
                '--plugin notinstalled {0}'.format(self.gitrepodir))

        # A plugin which is not installed was requested so not output
        self.assertEqual('', self.output)

    def test_handles_error(self):
        """
        An un-initialized jig Git repository provides an error message.
        """
        with self.assertRaises(ForcedExit):
            self.run_command(mkdtemp())

        self.assertResults(
            result_with_hint(
                u'This repository has not been initialized.',
                GIT_REPO_NOT_INITIALIZED),
            self.error)
