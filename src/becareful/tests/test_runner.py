from nose.plugins.attrib import attr

from becareful.tests.testcase import RunnerTestCase
from becareful.exc import RunnerExit
from becareful.plugins import initializer


class TestRunnerFromHook(RunnerTestCase):

    """


    """
    def test_uninitialized_repo(self):
        """
        The BC directory has not been initialized.
        """
        with self.assertRaises(RunnerExit) as ec:
            self.runner.fromhook(self.gitrepodir)

        self.assertEqual(1, ec.exception.message)
        self.assertEqual(self.error, 'This repository has not been '
            'initialized. Run becareful init GITREPO to set it up')

    def test_no_plugins(self):
        """
        If there is a BC directory without any plugins.
        """
        config = initializer(self.gitrepodir)

        with self.assertRaises(RunnerExit) as ec:
            self.runner.fromhook(self.gitrepodir)

        self.assertEqual(1, ec.exception.message)
        self.assertEqual(self.error, 'There are no plugins installed, '
            'use becareful install to add some')

    @attr('focus')
    def test_no_diff(self):
        pass
