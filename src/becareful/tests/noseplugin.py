"""
A nose plugin to ease some testing pain.
"""
import sys
from os import makedirs
from os.path import dirname, join, isdir, realpath
from shutil import rmtree
from subprocess import call, PIPE

from nose.plugins.base import Plugin


class TestSetupError(Exception):

    """
    Indicate that something went wrong while we were trying to setup.

    """
    pass


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

        try:
            setattr(test.test, 'gitrepodir',
                self._create_git_repo())
        except Exception as e:
            print(e)

    def afterTest(self, test):
        """
        Called after the test ran.
        """
        rmtree(test.test.gitrepodir)

    def _create_git_repo(self):
        testrepos = ['..'] * 3 + ['.testrepos']
        repo_harness_dir = join(dirname(__file__), *testrepos)

        try:
            repo = join(repo_harness_dir, 'repo')
            if isdir(repo):
                rmtree(repo)
            makedirs(repo)
        except:
            raise TestSetupError('Tried to create a directory to hold '
                'the test repositories and could not')

        retcode = call(['git', 'init', repo],
            stdin=PIPE, stdout=PIPE, stderr=PIPE)

        if retcode != 0:
            raise TestSetupError('Could not initialize a Git repository to '
                'run tests, is Git installed?')

        return realpath(repo)
