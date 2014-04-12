"""
A nose plugin to ease some testing pain.
"""
from os import listdir, mkdir
from os.path import join, realpath, isdir, expanduser
from tempfile import mkdtemp
from shutil import rmtree
from subprocess import call, PIPE

from nose.plugins.base import Plugin


def _create_git_repo_property(repo_harness_dir):
    """
    Property object to lazy git init a directory in ``repo_harness_dir``.
    """
    from jig.conf import JIG_DIR_NAME

    def getter(self):
        try:
            return self._gitrepodir
        except AttributeError:
            pass

        try:
            rhd = realpath(repo_harness_dir)
            if not isdir(rhd):
                mkdir(rhd)
            repo = mkdtemp(dir=rhd)
        except:
            raise TestSetupError(
                'Tried to create a directory to hold '
                'the test repositories and could not.')

        retcode = call(
            ['git', 'init', repo],
            stdin=PIPE, stdout=PIPE, stderr=PIPE)

        exclude_file = join(repo, '.git', 'info', 'exclude')

        # Ignore .jig so this directory will be clean
        with open(exclude_file, 'w') as fh:
            fh.write(JIG_DIR_NAME)

        if retcode != 0:
            raise TestSetupError(
                'Could not initialize a Git repository to '
                'run tests, is Git installed?')

        self._gitrepodir = repo

        return repo

    def setter(self, value):
        self._gitrepodir = value

    def deleter(self):
        try:
            rmtree(self._gitrepodir)
        except (AttributeError, OSError):
            pass

        try:
            delattr(self, '_gitrepodir')
        except AttributeError:
            pass

    return property(getter, setter, deleter)


class TestSetupError(Exception):

    """
    Indicate that something went wrong while we were trying to setup.

    """
    pass


class TestSetup(Plugin):

    """
    Provides some testing harness for jig tests runs.

    """
    enabled = True
    name = 'jig'
    score = 500

    def __init__(self):
        super(TestSetup, self).__init__()

        self.repo_harness_dir = mkdtemp()

    def options(self, parser, env):
        """
        Required by Nose to add options.
        """
        parser.add_option(
            '--unicodenazi', default=False,
            action='store_true', help='Turn unicode-nazi on'
        )

    def configure(self, options, conf):
        """
        Required by Nose to configure the plugin.
        """
        if options.unicodenazi:
            # Turn on unicode-nazi to catch unicode/str comparisons
            __import__('unicodenazi')

    def beforeTest(self, test):
        """
        Called before each test is ran.
        """
        try:
            # Delete existing ~/.gitconfig
            with open(expanduser('~/.gitconfig'), 'w') as fh:
                fh.write('')

            # Set a descriptor on the class to lazy-create our git repo dir
            setattr(
                test.test.__class__, 'gitrepodir',
                _create_git_repo_property(self.repo_harness_dir)
            )
        except Exception as e:
            print(e)

    def afterTest(self, test):
        """
        Called after the test ran.
        """
        del test.test.gitrepodir

    def finalize(self, result):
        """
        Called after all tests have ran and output is collected.
        """
        for path in listdir(self.repo_harness_dir):
            rmtree(join(self.repo_harness_dir, path))

        return None
