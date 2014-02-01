# coding=utf-8
from jig.exc import ForcedExit
from jig.tests.testcase import (
    CommandTestCase, PluginTestCase, result_with_hint)
from jig.plugins import set_jigconfig
from jig.output import ATTENTION
from jig.commands import report


class TestReportCommand(CommandTestCase, PluginTestCase):

    """
    Test the report command.

    """
    command = report.Command

    def setUp(self):
        super(TestReportCommand, self).setUp()

        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create a few commits
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.commit(self.gitrepodir, 'b.txt', 'b')
        self.commit(self.gitrepodir, 'c.txt', 'c')

    def test_cannot_resolve_revision_range(self):
        """
        Given a range that is invalid it notifies the user.
        """
        with self.assertRaises(ForcedExit) as ec:
            self.run_command('--rev-range FOO..BAR {0}'.format(self.gitrepodir))

        self.assertEqual(1, ec.exception.message)

        self.assertTrue(self.error)

    def test_reports_one_commit(self):
        """
        With a range indicating one commit it reports on that one.
        """
        with self.assertRaises(SystemExit) as ec:
            self.run_command('--rev-range HEAD^1..HEAD {0}'.format(self.gitrepodir))

        self.assertEqual(0, ec.exception.message)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: c.txt
                c is +

            {0}  Jig ran 1 plugin
                Info 0 Warn 1 Stop 0
            """.format(ATTENTION), self.output)

    def test_defaults_latest_commit(self):
        """
        Without a revision range it uses HEAD^1..HEAD.
        """
        with self.assertRaises(SystemExit) as ec:
            self.run_command('{0}'.format(self.gitrepodir))

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: c.txt
                c is +

            {0}  Jig ran 1 plugin
                Info 0 Warn 1 Stop 0
            """.format(ATTENTION), self.output)

    def test_reports_two_commits(self):
        """
        With a range indicating two commits it reports on both.
        """
        with self.assertRaises(SystemExit) as ec:
            self.run_command('--rev-range HEAD~2..HEAD {0}'.format(self.gitrepodir))

        self.assertEqual(0, ec.exception.message)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: c.txt
                c is +

            ⚠  line 1: b.txt
                b is +

            {0}  Jig ran 1 plugin
                Info 0 Warn 2 Stop 0
            """.format(ATTENTION), self.output)

    def test_reports_only_one_plugin(self):
        """
        If a plugin is given it will only report on that plugin.
        """
        with self.assertRaises(SystemExit) as ec:
            self.run_command('--plugin plugin01 --rev-range HEAD^1..HEAD {0}'.format(self.gitrepodir))

        self.assertEqual(0, ec.exception.message)

        self.assertResults(u"""
            ▾  plugin01

            ⚠  line 1: c.txt
                c is +

            {0}  Jig ran 1 plugin
                Info 0 Warn 1 Stop 0
            """.format(ATTENTION), self.output)
