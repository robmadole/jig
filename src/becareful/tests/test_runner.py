from shutil import rmtree
from os.path import join

from mock import patch

from becareful.tests.testcase import RunnerTestCase, PluginTestCase
from becareful.tests.mocks import MockPlugin
from becareful.exc import ForcedExit
from becareful.plugins import set_bcconfig, Plugin


class TestRunnerFromHook(RunnerTestCase, PluginTestCase):

    """
    Runner hook is used by the command line script to run BeCareful.

    """
    def setUp(self):
        super(TestRunnerFromHook, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.testrepo = repo
        self.testrepodir = working_dir
        self.testdiffs = diffs

    def test_simple_integration(self):
        with patch.object(self.runner, 'results'):
            plugin = MockPlugin()
            # Empty results
            self.runner.results.return_value = {plugin:
                (0, '', '')}

            self.runner.fromhook(self.gitrepodir)

            self.assertEqual(
                'Ran 1 plugin, nothing to report\n',
                self.output)


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
        The BC directory has not been initialized.
        """
        # Remove the .bc directory, effectively un-initializing our repository
        rmtree(join(self.gitrepodir, '.bc'))

        with self.assertRaises(ForcedExit) as ec:
            self.runner.results(self.gitrepodir)

        self.assertEqual(1, ec.exception.message)
        self.assertEqual('This repository has not been initialized. Run '
            'becareful init GITREPO to set it up\n',
            self.error)

    def test_no_plugins(self):
        """
        If there is a BC directory without any plugins.
        """
        with self.assertRaises(ForcedExit) as ec:
            self.runner.results(self.gitrepodir)

        self.assertEqual(1, ec.exception.message)
        self.assertEqual('There are no plugins installed, use becareful '
            'install to add some\n',
            self.error)

    def test_empty_repository(self):
        """
        If BC is ran on a repository that hasn't had any commits
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        self.runner.results(self.gitrepodir)

        self.assertEqual('This repository is empty, BeCareful needs at '
            'least 1 commit to continue\n',
            self.output)

    def test_no_diff(self):
        """
        If BC is ran on a repository without any changes.
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        self.commit(self.gitrepodir,
            name='a.txt',
            content='a')

        self.runner.results(self.gitrepodir)

        self.assertEqual('No staged changes in the repository, skipping '
            'BeCareful\n',
            self.output)

    def test_unstaged_one_file(self):
        """
        Ran on a repository with an unstaged file.
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

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
            'BeCareful\n',
            self.output)

    def test_staged_one_file(self):
        """
        Ran on a repository with a staged file.
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

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
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

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
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

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

            self._add_plugin(self.bcconfig, 'plugin01')
            set_bcconfig(self.gitrepodir, config=self.bcconfig)

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
        Supports non-JSON output from the plugin.
        """
        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (
                1, '', 'Something went horribly wrong')

            self._add_plugin(self.bcconfig, 'plugin01')
            set_bcconfig(self.gitrepodir, config=self.bcconfig)

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
