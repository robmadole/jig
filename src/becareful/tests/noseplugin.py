"""
A nose plugin to ease some testing pain.
"""
from os import listdir, mkdir
from os.path import dirname, join, realpath, isdir
from tempfile import mkdtemp
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

        testrepos = ['..'] * 3 + ['.testrepos']
        self.repo_harness_dir = join(dirname(__file__), *testrepos)

    def options(self, parser, env):
        """
        Required by Nose to add options.
        """
        parser.add_option('--unicodenazi', default=False,
            action='store_true', help='Turn unicode-nazi on')

    def configure(self, options, conf):
        """
        Required by Nose to configure the plugin.
        """
        if options.unicodenazi:
            # Turn on unicode-nazi to catch unicode/str comparisons
            __import__(unicodenazi)

    def beforeTest(self, test):
        """
        Called before each test is ran.
        """
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

    def finalize(self, result):
        """
        Called after all tests have ran and output is collected.
        """
        for path in listdir(self.repo_harness_dir):
            rmtree(join(self.repo_harness_dir, path))

        return None

    def _create_git_repo(self):
        """
        Create an empty Git repository in the .testrepos directory.

        Returns the full path to the newly created directory.
        """
        try:
            rhd = realpath(self.repo_harness_dir)
            if not isdir(rhd):
                mkdir(rhd)
            repo = mkdtemp(dir=rhd)
        except:
            raise TestSetupError('Tried to create a directory to hold '
                'the test repositories and could not')

        retcode = call(['git', 'init', repo],
            stdin=PIPE, stdout=PIPE, stderr=PIPE)

        if retcode != 0:
            raise TestSetupError('Could not initialize a Git repository to '
                'run tests, is Git installed?')

        return repo
