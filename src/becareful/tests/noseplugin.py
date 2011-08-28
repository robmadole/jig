"""
A nose plugin to ease some testing pain.
"""
from nose.plugins.base import Plugin


class TestSetup(Plugin):

    """
    Provides some testing harness for BeCareful tests runs.

    """
    enabled = True
    name = 'becareful'
    score = 500

    def __init__(self):
        super(TestSetup, self).__init__()

    def options(self, parser, env):
        """
        Required by Nose to add options.
        """
        pass

    def configure(self, options, conf):
        """
        Required by Nose to configure the plugin.
        """
        pass

    def beforeTest(self, test):
        """
        Called before each test is ran.
        """
        testmethod = getattr(test.test, test.test._testMethodName)

        setattr(test.test, 'gitrepodir',
            self._create_git_repo())

    def _create_git_repo(self):
        pass
