# coding=utf-8
import sys
from tempfile import mkdtemp
from os.path import isfile, join

from mock import Mock

from jig.tests.testcase import (
    JigTestCase, CommandTestCase, cd_gitrepo)
from jig.plugins import create_plugin, get_jigconfig, PluginManager
from jig.gitutils.commands import git
from jig.exc import ForcedExit
from jig.commands import ci


class TestWhenExitsZero(JigTestCase):

    """
    Test for the utility that catches SystemExit and cals a function.

    """
    def test_does_not_call(self):
        """
        Doesn't call the passed function if the exit code is non-zero.
        """
        call_if_ok = Mock()

        with self.assertRaises(SystemExit):
            with ci._when_exits_zero(call_if_ok):
                sys.exit(1)

        self.assertFalse(call_if_ok.called)

    def test_does_call(self):
        """
        Calls the passed function if the exit code is zero.
        """
        call_if_ok = Mock()

        with self.assertRaises(SystemExit):
            with ci._when_exits_zero(call_if_ok):
                sys.exit(0)

        self.assertTrue(call_if_ok.called)


class TestCiCommand(CommandTestCase):

    """
    Test the ci subcommand.

    """
    command = ci.Command

    def setUp(self):
        super(TestCiCommand, self).setUp()

        self.plugindir = mkdtemp()

        self.pluginpath = create_plugin(
            self.plugindir, template='python',
            bundle='a', name='a'
        )

        self.commit(self.gitrepodir, '.jigplugins.txt', self.pluginpath)

    def run_first_time(self):
        try:
            self.run_command('{0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )
        except ForcedExit:
            pass

        # Reset the buckets used to collect output
        self.view.init_collector()

    @cd_gitrepo
    def test_initializes_path(self):
        with self.assertRaises(ForcedExit):
            self.run_command('{0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )

        self.assertTrue(isfile(join(self.gitrepodir, '.jig', 'plugins.cfg')))

    @cd_gitrepo
    def test_installs_plugins(self):
        with self.assertRaises(ForcedExit):
            self.run_command('{0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )

        pm = PluginManager(get_jigconfig(self.gitrepodir))

        plugin = pm.plugins[0]

        # This was the plugin that was installed in our setUp
        self.assertEqual('a', plugin.name)

        self.assertResults(
            u'''
            From {0}:
             - Added plugin a in bundle a
            '''.format(self.pluginpath),
            self.output
        )

    @cd_gitrepo
    def test_sets_tracking_branch(self):
        with self.assertRaises(ForcedExit):
            self.run_command('{0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )

        rev_parse = git(self.gitrepodir).bake('rev-parse')

        self.assertEqual(
            rev_parse('master'),
            rev_parse('jig-ci-last-run')
        )

        self.assertResults(
            u'First run, tracking branch created for HEAD',
            self.error
        )

    @cd_gitrepo
    def test_sets_tracking_branch_explicit(self):
        tracking_branch = 'jig-custom'

        with self.assertRaises(ForcedExit):
            self.run_command('--tracking-branch {0} {1} {2}'.format(
                tracking_branch, '.jigplugins.txt', self.gitrepodir)
            )

        rev_parse = git(self.gitrepodir).bake('rev-parse')

        self.assertEqual(
            rev_parse('master'),
            rev_parse(tracking_branch)
        )

    @cd_gitrepo
    def test_runs_after_commit(self):
        self.run_first_time()

        self.commit(self.gitrepodir, 'a.txt', 'a')

        with self.assertRaises(SystemExit):
            self.run_command('{0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )

    @cd_gitrepo
    def test_uses_default_tap_formatter(self):
        self.run_first_time()

        self.commit(self.gitrepodir, 'a.txt', 'a')

        with self.assertRaises(SystemExit):
            self.run_command('{0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )

        # This is a marker of TAP output
        self.assertIn('TAP version 13', self.output)

    @cd_gitrepo
    def test_uses_alternative_formatter(self):
        self.run_first_time()

        self.commit(self.gitrepodir, 'a.txt', 'a')

        with self.assertRaises(SystemExit):
            self.run_command('--format fancy {0} {1}'.format(
                '.jigplugins.txt', self.gitrepodir)
            )

        # This is a marker that will be present from the fancy formatter
        self.assertIn(u'\U0001f449  Jig ran 1 plugin', self.output)
