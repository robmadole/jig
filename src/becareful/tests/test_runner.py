from becareful.tests.testcase import RunnerTestCase
from becareful.plugins import initializer


class TestRunnerFromHook(RunnerTestCase):
    def test_uninitialized_repo(self):
        """
        The BC directory has not been initialized.
        """
        self.runner.fromhook(self.gitrepodir)

        self.assertEqual(self.error, 'This repository has not been initialized. Run '
            'becareful init GITREPO to set it up')

    def test_no_plugins(self):
        """
        If there is a BC directory without any plugins.
        """
        config = initializer(self.gitrepodir)

        self.runner.fromhook(self.gitrepodir)
