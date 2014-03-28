from shutil import rmtree
from os.path import join
from contextlib import nested
from datetime import datetime, timedelta

from mock import patch

from jig.tests.testcase import (
    RunnerTestCase, PluginTestCase, result_with_hint)
from jig.conf import PLUGIN_CHECK_FOR_UPDATES
from jig.commands.hints import GIT_REPO_NOT_INITIALIZED
from jig.tests.mocks import MockPlugin
from jig.exc import ForcedExit
from jig.plugins import set_jigconfig, Plugin
from jig.runner import Runner
from jig.gitutils.branches import parse_rev_range


class TestRunner(RunnerTestCase, PluginTestCase):

    """
    Runner is used by the command line script to run jig.

    """
    def setUp(self):
        super(TestRunner, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

    def test_simple_integration(self):
        """
        Will run the hook.
        """
        with patch.object(self.runner, 'results'):
            plugin = MockPlugin()
            # Empty results
            self.runner.results.return_value = {
                plugin: (0, '', '')}

            with self.assertRaises(SystemExit) as ec:
                self.runner.fromhook(self.gitrepodir)  # pragma: no branch

            self.assertSystemExitCode(ec.exception, 0)

            self.assertEqual(
                u'\U0001f44c  Jig ran 1 plugin, nothing to report\n',
                self.output)

    def test_uninitialized_repo(self):
        """
        The .jig directory has not been initialized.
        """
        # Remove the .jig directory, effectively un-initializing our repository
        rmtree(join(self.gitrepodir, '.jig'))

        with self.assertRaises(ForcedExit) as ec:
            self.runner.fromhook(self.gitrepodir)  # pragma: no branch

        self.assertSystemExitCode(ec.exception, 1)

        self.assertResults(
            result_with_hint(
                u'This repository has not been initialized.',
                GIT_REPO_NOT_INITIALIZED),
            self.error)

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
                self.runner.main(self.gitrepodir)

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

            self.runner.main(self.gitrepodir)

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

            self.runner.main(self.gitrepodir)

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

            self.runner.main(self.gitrepodir)

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

            self.runner.main(self.gitrepodir)

        # We exited with 1 to indicate the commit should abort
        r_sys.exit.assert_called_once_with(1)


class TestRunnerPluginUpdates(RunnerTestCase, PluginTestCase):

    """
    From the hook the plugins can be updated.

    """
    def setUp(self):
        super(TestRunnerPluginUpdates, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        targets = (
            'jig.runner.sys',
            'jig.runner.datetime',
            'jig.runner.plugins_have_updates',
            'jig.runner.set_jigconfig',
            'jig.runner.set_checked_for_updates',
            ('jig.runner.raw_input', {'create': True}),
            'jig.runner.update_plugins')

        self._patches = []
        for target in targets:
            if isinstance(target, tuple):
                patched = patch(target[0], **target[1])
                target = target[0]
            else:
                patched = patch(target)

            self._patches.append(patched)

            basename = target.split('.')[-1]
            setattr(self, basename, patched.start())

        # For all tests, make the current date in the future
        self.datetime.utcnow.return_value = datetime.utcnow() + \
            PLUGIN_CHECK_FOR_UPDATES + timedelta(days=1)

    def tearDown(self):
        for patched in self._patches:
            patched.stop()

    def test_non_interactive(self):
        """
        Doesn't check if interactive is False.
        """
        self.runner.main(self.gitrepodir, interactive=False)

    def test_never_been_checked(self):
        """
        For existing Jig installations, there will be no last checked value.
        """
        # There are no updates for the plugins
        self.plugins_have_updates.return_value = False

        with patch('jig.runner.last_checked_for_updates') as lcu:
            # If there is no value for the last time a repository was checked
            # it will return 0.
            lcu.return_value = 0

            self.runner.main(self.gitrepodir)

        # The check to see if the plugins have updates was called
        self.assertTrue(self.plugins_have_updates.called)

    def test_checks_for_updates(self):
        """
        Will check for updates if it has been a while.
        """
        # There are no updates for the plugins
        self.plugins_have_updates.return_value = False

        self.runner.main(self.gitrepodir)

        # The plugins were checked to see if there is an update
        self.assertTrue(self.plugins_have_updates.called)

        # Since they were checked, the date was also moved forward
        self.assertTrue(self.set_checked_for_updates.called)

        # Things exited normally
        self.sys.exit.assert_called_with(0)

    def test_prompts_user_to_update(self):
        """
        Will ask to install updates but the answer is no.
        """
        # This time there are updates to install
        self.plugins_have_updates.return_value = True

        # The answer will be "n"
        self.raw_input.side_effect = ['n']

        self.runner.main(self.gitrepodir)

        # They did give a valid answer, so the date was moved
        self.assertTrue(self.set_checked_for_updates.called)

        # The plugins were not updated though
        self.assertFalse(self.update_plugins.called)

    def test_prompts_until_they_answer_correctly(self):
        """
        Continues until a proper answer is given to the question.
        """
        self.plugins_have_updates.return_value = True

        # Answer a couple of times with junk, and then say no
        self.raw_input.side_effect = ['junk', 'foo', 'n']

        self.runner.main(self.gitrepodir)

        # The question was asked until a proper response was given
        self.assertEqual(3, self.raw_input.call_count)

    def test_keyboard_interrupt(self):
        """
        While being asked a question CTRL-C is pressed.
        """
        self.plugins_have_updates.return_value = True

        # Answer a couple of times with junk, and then say no
        self.raw_input.side_effect = KeyboardInterrupt

        self.runner.main(self.gitrepodir)

        # It exited just fine, no errors
        self.sys.exit.assert_called_with(0)

        # Since it was a CTRL-C, we shouldn't move the date forward
        self.assertFalse(self.set_checked_for_updates.called)

        # And the plugins were not updated
        self.assertFalse(self.update_plugins.called)

    def test_will_update_plugins(self):
        """
        If the answer is yes, the plugins are updated.
        """
        self.plugins_have_updates.return_value = True

        # The answer to update the plugins is yes
        self.raw_input.return_value = 'y'

        self.runner.main(self.gitrepodir)

        # Exited normally
        self.sys.exit.assert_called_with(0)

        # We moved the next date the plugins should be checked forward
        self.assertTrue(self.set_jigconfig.called)
        self.assertTrue(self.set_checked_for_updates.called)

        # And the plugins were updated
        self.assertTrue(self.update_plugins.called)


class TestRunnerResults(RunnerTestCase, PluginTestCase):

    """
    Can the runner iterate over the plugins and gather results.

    """
    def setUp(self):
        super(TestRunnerResults, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

    def test_no_plugins(self):
        """
        If there is a .jig directory without any plugins.
        """
        self.runner.results(self.gitrepodir)

        self.assertEqual(
            'There are no plugins installed, use jig '
            'install to add some.\n',
            self.output
        )

    def test_empty_repository(self):
        """
        If .jig is ran on a repository that hasn't had any commits
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.runner.results(self.gitrepodir)

        self.assertEqual(
            'This repository is empty, jig needs at '
            'least 1 commit to continue.\n',
            self.output
        )

    def test_no_diff(self):
        """
        If .jig is ran on a repository without any changes.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.commit(
            self.gitrepodir,
            name='a.txt',
            content='a'
        )

        self.runner.results(self.gitrepodir)

        self.assertEqual(
            'No staged changes in the repository, skipping jig.\n',
            self.output
        )

    def test_unstaged_one_file(self):
        """
        Ran on a repository with an unstaged file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Add the first commit because we have to have it
        self.commit(
            self.gitrepodir,
            name='a.txt',
            content='a'
        )

        # We've created this but not added it to the index
        self.create_file(
            self.gitrepodir,
            name='b.txt',
            content='b'
        )

        self.runner.results(self.gitrepodir)

        self.assertEqual(
            'No staged changes in the repository, skipping jig.\n',
            self.output
        )

    def test_staged_one_file(self):
        """
        Ran on a repository with a staged file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        # Add the first commit because we have to have it
        self.commit(
            self.gitrepodir,
            name='a.txt',
            content='a'
        )

        # Create a new file an stage it to the index
        self.stage(
            self.gitrepodir,
            name='b.txt',
            content='b'
        )

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
        self.commit(
            self.gitrepodir,
            name='a.txt',
            content='a'
        )

        # We've created this but not added it to the index
        self.stage(
            self.gitrepodir,
            name='a.txt',
            content='aaa'
        )

        results = self.runner.results(self.gitrepodir)

        _, stdout, _ = results.items()[0][1]

        self.assertEqual(
            {u'a.txt': [[1, u'warn', u'a is -'],
                        [1, u'warn', u'aaa is +']]},
            stdout
        )

    def test_deleted_one_file(self):
        """
        Delete one file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.commit(
            self.gitrepodir,
            name='a.txt',
            content='a'
        )

        # Now stage a file for removal
        self.stage_remove(self.gitrepodir, name='a.txt')

        results = self.runner.results(self.gitrepodir)

        _, stdout, _ = results.items()[0][1]

        # We should see it being removed
        self.assertEqual({u'a.txt': [[1, u'warn', u'a is -']]}, stdout)

    def test_specific_plugin(self):
        """
        Filter to results to a specific file.
        """
        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        self.commit(
            self.gitrepodir,
            name='a.txt',
            content='a'
        )

        self.stage(
            self.gitrepodir,
            name='b.txt',
            content='b'
        )

        # We can filter to the one that is already installed
        self.assertEqual(
            1,
            len(self.runner.results(self.gitrepodir, plugin='plugin01'))
        )

        # If we try to filter on a non-existent plugin we get no results
        self.assertEqual(
            0,
            len(self.runner.results(self.gitrepodir, plugin='notinstalled'))
        )

    def test_handles_non_json_stdout(self):
        """
        Supports non-JSON output from the plugin.
        """
        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (
                0, 'Test non-JSON output', ''
            )

            self._add_plugin(self.jigconfig, 'plugin01')
            set_jigconfig(self.gitrepodir, config=self.jigconfig)

            self.commit(
                self.gitrepodir,
                name='a.txt',
                content='a'
            )

            self.stage(
                self.gitrepodir,
                name='b.txt',
                content='b'
            )

            results = self.runner.results(self.gitrepodir)

            _, stdout, _ = results.items()[0][1]

        # And we can still get the output even though it's not JSON
        self.assertEqual('Test non-JSON output', stdout)

    def test_handles_retcode_1_with_stderr(self):
        """
        Handles non-zero return codes and data written to stderr.
        """
        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (
                1, '', 'Something went horribly wrong')

            self._add_plugin(self.jigconfig, 'plugin01')
            set_jigconfig(self.gitrepodir, config=self.jigconfig)

            self.commit(
                self.gitrepodir,
                name='a.txt',
                content='a')

            self.stage(
                self.gitrepodir,
                name='b.txt',
                content='b')

            results = self.runner.results(self.gitrepodir)

            retcode, _, stderr = results.items()[0][1]

        self.assertEqual(1, retcode)
        self.assertEqual(
            'Something went horribly wrong',
            stderr
        )


class TestRunnerRevRange(RunnerTestCase, PluginTestCase):

    """
    Runner will take an options revision range instead of using staged files.

    """
    def setUp(self):
        super(TestRunnerRevRange, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self._add_plugin(self.jigconfig, 'plugin01')
        set_jigconfig(self.gitrepodir, config=self.jigconfig)

        for letter in ['a', 'b', 'c']:
            self.commit(
                self.gitrepodir,
                name='{0}.txt'.format(letter),
                content=letter
            )

    def file_changes(self, results):
        """
        Get the file changes for the given results.
        """
        return results.items()[0][1][1]

    def test_bad_rev_range_format(self):
        """
        If a range is not formatted correctly.
        """
        with self.assertRaises(ForcedExit):
            self.runner.main(
                self.gitrepodir,
                rev_range='BAR:BAZ',
                interactive=False
            )

        self.assertEqual(
            'BAR:BAZ\n\nThe revision range is not in a valid format.\n\n'
            'Use "REV_A..REV_B" to specify the revisions that Jig should operate '
            'against.\n',
            self.error
        )

    def test_non_existent_rev_range(self):
        """
        If a range is given that does not exist.
        """
        with self.assertRaises(ForcedExit):
            self.runner.main(
                self.gitrepodir,
                rev_range='FOO..BAR',
                interactive=False
            )

        self.assertEqual(
            'FOO..BAR\n\nThe revision specified is formatted correctly but one '
            'of both of the revisions\ncould not be found.\n',
            self.error
        )

    def test_existing_rev_range(self):
        """
        Valid revision range returns results.
        """
        results = self.runner.results(
            self.gitrepodir,
            rev_range=parse_rev_range(self.gitrepodir, 'HEAD^1..HEAD')
        )

        self.assertEqual(1, len(self.file_changes(results)))

    def test_multiple_rev_range(self):
        """
        Valid revision that includes two changes returns both.
        """
        results = self.runner.results(
            self.gitrepodir,
            rev_range=parse_rev_range(self.gitrepodir, 'HEAD~2..HEAD')
        )

        self.assertEqual(2, len(self.file_changes(results)))
