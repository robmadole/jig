from shutil import rmtree
from os.path import join
from contextlib import nested

from mock import patch

from jig.tests.testcase import (
    RunnerTestCase, PluginTestCase, result_with_hint)
from jig.commands.hints import GIT_REPO_NOT_INITIALIZED
from jig.tests.mocks import MockPlugin
from jig.exc import ForcedExit
from jig.plugins import set_jigconfig, Plugin
from jig.runner import Runner


class TestRunnerEntryPoints(RunnerTestCase, PluginTestCase):

    """
    Runner hook is used by the command line script to run jig.

    """
    def setUp(self):
        super(TestRunnerEntryPoints, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.testrepo = repo
        self.testrepodir = working_dir
        self.testdiffs = diffs

    def test_simple_integration(self):
        """
        Will run the hook.
        """
        with patch.object(self.runner, 'results'):
            plugin = MockPlugin()
            # Empty results
            self.runner.results.return_value = {plugin:
                (0, '', '')}

            with self.assertRaises(SystemExit) as ec:
                self.runner.fromhook(self.gitrepodir)  # pragma: no branch

            self.assertSystemExitCode(ec.exception, 0)

            self.assertEqual(
                u'\U0001f44c  Jig ran 1 plugin, nothing to report\n',
                self.output)

    def test_will_not_prompt_if_no_messages(self):
        """
        No prompt is presented if there are no messages to communicate.
        """
        with patch.object(Runner, 'results'):
            # No results came back from any plugin
            Runner.results.return_value = []

            with nested(
                patch('jig.runner.raw_input', create=True),
                patch('jig.runner.sys'),
                self.assertRaises(SystemExit)
            ) as (ri, r_sys, ec):
                r_sys.exit.side_effect = SystemExit
                self.runner.fromhook(self.gitrepodir)

        # Make sure that the call to raw_input never happened
        self.assertFalse(ri.called)

        # And we exited with 0 because there is no reason to stop the commit
        r_sys.exit.assert_called_once_with(0)

    def test_will_prompt_user(self):
        """
        User sees a prompt if there are messages.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.raw_input', create=True),
            patch('jig.runner.sys'),
            self.assertRaises(SystemExit)
        ) as (ri, r_sys, ec):
            # Fake the raw_input call to return 's'
            r_sys.exit.side_effect = SystemExit
            ri.return_value = 's'

            self.runner.fromhook(self.gitrepodir)

        # The user was prompted about committing or canceling
        ri.assert_called_once_with(
            '\nCommit anyway (hit "c"), or stop (hit "s"): ')
        # When they said cancel we exited with non-zero
        r_sys.exit.assert_called_once_with(1)

    def test_will_prompt_but_continue_anyway(self):
        """
        The user can choose to continue with the commit anyway.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.raw_input', create=True),
            patch('jig.runner.sys')
        ) as (ri, r_sys):
            # Fake the raw_input call to return 'c'
            ri.return_value = 'c'

            self.runner.fromhook(self.gitrepodir)

        # The user was prompted about committing or canceling
        ri.assert_called_once_with(
            '\nCommit anyway (hit "c"), or stop (hit "s"): ')
        # When they said cancel we exited with non-zero
        r_sys.exit.assert_called_once_with(0)

    def test_will_continue_to_prompt_until_correctly_answered(self):
        """
        The user must answer 'c' or 's' and nothing else.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.raw_input', create=True),
            patch('jig.runner.sys')
        ) as (ri, r_sys):
            # Fake the raw_input call to return 'c' only after giving
            # two incorrect options.
            ri.side_effect = ['1', '2', 'c']

            self.runner.fromhook(self.gitrepodir)

        # raw_input was called 3 times until it received a proper response
        self.assertEqual(3, ri.call_count)

    def test_will_abort_on_keyboard_interrupt(self):
        """
        The user can CTRL-C out of it and the commit is canceled.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Create staged changes
        self.commit(self.gitrepodir, 'a.txt', 'a')
        self.stage(self.gitrepodir, 'b.txt', 'b')

        with nested(
            patch('jig.runner.raw_input', create=True),
            patch('jig.runner.sys'),
            self.assertRaises(SystemExit)
        ) as (ri, r_sys, ec):
            # Fake the raw_input call to return 'c'
            ri.side_effect = KeyboardInterrupt
            r_sys.exit.side_effect = SystemExit

            self.runner.fromhook(self.gitrepodir)

        # We exited with 1 to indicate the commit should abort
        r_sys.exit.assert_called_once_with(1)


class TestRunnerResults(RunnerTestCase, PluginTestCase):

    """
    Can the runner iterate over the plugins and gather results.

    """
    def setUp(self):
        super(TestRunnerResults, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.testrepo = repo
        self.testrepodir = working_dir
        self.testdiffs = diffs

    def test_uninitialized_repo(self):
        """
        The .jig directory has not been initialized.
        """
        # Remove the .jig directory, effectively un-initializing our repository
        rmtree(join(self.gitrepodir, '.jig'))

        with self.assertRaises(ForcedExit) as ec:
            self.runner.results(self.gitrepodir)

        self.assertEqual('1', str(ec.exception))
        self.assertResults(
            result_with_hint(
                u'This repository has not been initialized.',
                GIT_REPO_NOT_INITIALIZED),
            self.error)

    def test_no_plugins(self):
        """
        If there is a .jig directory without any plugins.
        """
        self.runner.results(self.gitrepodir)

        self.assertEqual('There are no plugins installed, use jig '
            'install to add some.\n',
            self.output)

    def test_empty_repository(self):
        """
        If .jig is ran on a repository that hasn't had any commits
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.runner.results(self.gitrepodir)

        self.assertEqual('This repository is empty, jig needs at '
            'least 1 commit to continue.\n',
            self.output)

    def test_no_diff(self):
        """
        If .jig is ran on a repository without any changes.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.commit(self.gitrepodir,
            name='a.txt',
            content='a')

        self.runner.results(self.gitrepodir)

        self.assertEqual('No staged changes in the repository, skipping '
            'jig.\n',
            self.output)

    def test_unstaged_one_file(self):
        """
        Ran on a repository with an unstaged file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Add the first commit because we have to have it
        self.commit(self.gitrepodir,
            name='a.txt',
            content='a')

        # We've created this but not added it to the index
        self.create_file(self.gitrepodir,
            name='b.txt',
            content='b')

        self.runner.results(self.gitrepodir)

        self.assertEqual('No staged changes in the repository, skipping '
            'jig.\n',
            self.output)

    def test_staged_one_file(self):
        """
        Ran on a repository with a staged file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Add the first commit because we have to have it
        self.commit(self.gitrepodir,
            name='a.txt',
            content='a')

        # Create a new file an stage it to the index
        self.stage(self.gitrepodir,
            name='b.txt',
            content='b')

        results = self.runner.results(self.gitrepodir)

        # One plugin ran, we should have results from it
        self.assertEqual(1, len(results))

        # It's plugin01
        self.assertEqual('plugin01', results.keys()[0].name)

        retcode, stdout, stderr = results.items()[0][1]

        # The return code is 0
        self.assertEqual(0, retcode)
        # We auto-convert to an object
        self.assertEqual({u'b.txt': [[1, u'warn', u'b is +']]}, stdout)
        # And no errors occurred here
        self.assertEqual('', stderr)

    def test_modified_one_file(self):
        """
        One modified and staged file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Add the first commit because we have to have it
        self.commit(self.gitrepodir,
            name='a.txt',
            content='a')

        # We've created this but not added it to the index
        self.stage(self.gitrepodir,
            name='a.txt',
            content='aaa')

        results = self.runner.results(self.gitrepodir)

        _, stdout, _ = results.items()[0][1]

        self.assertEqual({u'a.txt': [[1, u'warn', u'a is -'], [1, u'warn',
            u'aaa is +']]}, stdout)

    def test_deleted_one_file(self):
        """
        Delete one file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.commit(self.gitrepodir,
            name='a.txt',
            content='a')

        # Now stage a file for removal
        self.stage_remove(self.gitrepodir, name='a.txt')

        results = self.runner.results(self.gitrepodir)

        _, stdout, _ = results.items()[0][1]

        # We should see it being removed
        self.assertEqual({u'a.txt': [[1, u'warn', u'a is -']]}, stdout)

    def test_handles_non_json_stdout(self):
        """
        Supports non-JSON output from the plugin.
        """
        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (
                0, 'Test non-JSON output', '')

            self._add_plugin(self.jigconfig, 'plugin01')
            set_jigconfig(self.gitrepodir, config=self.jigconfig)

            self.commit(self.gitrepodir,
                name='a.txt',
                content='a')

            self.stage(self.gitrepodir,
                name='b.txt',
                content='b')

            results = self.runner.results(self.gitrepodir)

            _, stdout, _ = results.items()[0][1]

        # And we can still get the output even though it's not JSON
        self.assertEqual('Test non-JSON output',
            stdout)

    def test_handles_retcode_1_with_stderr(self):
        """
        Handles non-zero return codes and data written to stderr.
        """
        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (
                1, '', 'Something went horribly wrong')

            self._add_plugin(self.jigconfig, 'plugin01')
            set_jigconfig(self.gitrepodir, config=self.jigconfig)

            self.commit(self.gitrepodir,
                name='a.txt',
                content='a')

            self.stage(self.gitrepodir,
                name='b.txt',
                content='b')

            results = self.runner.results(self.gitrepodir)

            retcode, _, stderr = results.items()[0][1]

        self.assertEqual(1, retcode)
        self.assertEqual('Something went horribly wrong',
            stderr)
