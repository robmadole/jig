from shutil import rmtree
from os.path import join

from nose.plugins.attrib import attr

from becareful.tests.testcase import RunnerTestCase, PluginTestCase
from becareful.exc import RunnerExit
from becareful.plugins import set_bcconfig


class TestRunnerFromHook(RunnerTestCase, PluginTestCase):

    """
    Test the interface to the BeCareful system.

    """
    def setUp(self):
        super(TestRunnerFromHook, self).setUp()

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

        with self.assertRaises(RunnerExit) as ec:
            self.runner.results(self.gitrepodir)

        self.assertEqual(1, ec.exception.message)
        self.assertEqual('This repository has not been initialized. Run '
            'becareful init GITREPO to set it up',
            self.error)

    def test_no_plugins(self):
        """
        If there is a BC directory without any plugins.
        """
        with self.assertRaises(RunnerExit) as ec:
            self.runner.results(self.gitrepodir)

        self.assertEqual(1, ec.exception.message)
        self.assertEqual('There are no plugins installed, use becareful '
            'install to add some',
            self.error)

    @attr('focus')
    def test_empty_repository(self):
        """
        If BC is ran on a repository that hasn't had any commits
        """
        self._add_plugin(self.bcconfig, 'plugin01')
        set_bcconfig(self.gitrepodir, config=self.bcconfig)

        self.runner.results(self.gitrepodir)

        self.assertEqual('This repository is empty, BeCareful needs at '
            'least 1 commit to continue',
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
            'BeCareful',
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
            'BeCareful',
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

        # We've created this but not added it to the index
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
        self.assertEqual({u'b.txt': []}, stdout)
        # And no errors occurred here
        self.assertEqual('', stderr)

    def test_modified_one_file(self):
        pass

    def test_deleted_one_file(self):
        pass

    def test_handles_non_json_stdout(self):
        pass

    def test_handles_retcode_1_with_stderr(self):
        pass
