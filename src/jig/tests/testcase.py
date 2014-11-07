# coding=utf-8
import shlex
from os import makedirs
from os.path import join, dirname
from subprocess import STDOUT, CalledProcessError
from functools import wraps
from StringIO import StringIO
from textwrap import dedent

from mock import patch

from jig.exc import ForcedExit
from jig.runner import Runner
from jig.plugins import initializer
from jig.diffconvert import GitDiffIndex
from jig.tools import NumberedDirectoriesToGit, cwd_bounce
from jig.output import strip_paint, ConsoleView, ResultsCollator


try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from subprocess import check_output
except ImportError:
    from jig.backports import check_output


def cd_gitrepo(func):
    """
    Change the current working directory to the test case's Git repository.

    This uses ``self.gitrepodir`` which is created by the
    :py:module:`jig.tests.noseplugin`.
    """
    @wraps(func)
    def wrapper(testcase, *args, **kwargs):
        with cwd_bounce(testcase.gitrepodir):
            func(testcase, *args, **kwargs)

    return wrapper


def result_with_hint(payload, hint):
    """
    Formats a one-line message with a hint.

    This is useful for testing the output of commands that utilize the
    :module:`jig.commands.hints` module.

    :param unicode payload: the first line of the result
    :param list hint: one of the attributes of :class:`jig.commands.hints`
    """
    return dedent(payload).strip() + u'\n' + hint


class JigTestCase(unittest.TestCase):

    """
    Base test case for all jig tests.

    """
    def setUp(self):
        self.fixturesdir = join(dirname(__file__), 'fixtures')

    def assertResults(self, expected, actual):
        """
        Assert that output matches expected argument.

        This method has some special handling intended to ease testing of the
        the output we get from :py:module:`jig.output`.

        As an example, it can be used like this::

            self.assertResults(u'''
                ▾  Plugin 1

                ✓  commit

                Ran 1 plugin
                    Info 1 Warn 0 Stop 0
                ''', self.output)

        This method will automatically dedent and strip the expected and clear
        off any console formatting characters (those that turn text colors or
        bold text).
        """
        expected = dedent(expected).strip()

        actual = strip_paint(actual.strip())

        self.assertEqual(expected, actual)

    def assertResultsIn(self, expected, actual):
        """
        Assert that a string is in the expected argument.
        """
        expected = dedent(expected).strip()

        actual = strip_paint(actual.strip())

        self.assertIn(expected, actual)

    def assertSystemExitCode(self, exception, code):
        """
        Assert that a :py:exception:`SystemExit` has a specific exit code.

        Note: this is Python 2.7/2.6 compatible since that exception changed
        slightly.
        """
        if hasattr(exception, 'code'):
            self.assertEqual(exception.code, code)
        elif isinstance(exception, ForcedExit):
            self.assertEqual(exception, ForcedExit(code))
        else:
            self.assertEqual(exception, code)

    def runcmd(self, cmd):
        """
        Takes a string and runs it, returning the output and exit code.

        Return is a tuple ``(exit_code, output_str)``.
        """
        cmd_args = shlex.split(cmd)

        try:
            output = check_output(cmd_args, stderr=STDOUT)
            retcode = 0
        except CalledProcessError as cpe:
            output = cpe.output
            retcode = cpe.returncode
        except OSError:
            output = None
            retcode = None

        return (retcode, output)

    def repo_from_fixture(self, repo_name):
        """
        Creates a ``git.Repo`` from the given fixture.

        The fixture should be a directory containing numbered directories
        suitable for creating a ``NumberedDirectoriesToGit``.

        Returns a tuple of 3 objects: repo, working_dir, diffs.
        """
        ndgit = NumberedDirectoriesToGit(
            join(self.fixturesdir, repo_name))

        repo = ndgit.repo

        return (ndgit.repo, repo.working_dir, ndgit.diffs())

    def git_diff_index(self, repo, diffs):
        """
        Retrieves the ``GitDiffIndex`` for the repository and diffs.
        """
        return GitDiffIndex(self.testrepodir, diffs)

    def create_file(self, gitrepodir, name, content):
        """
        Create or a file in the Git repository.

        The name of the file can contain directories, they will be created
        automatically.

        The directory ``gitrepodir`` represents the full path to the Git
        repository. ``name`` will be a string like ``a/b/c.txt``. ``content``
        will be written to the file.

        Return ``True`` if it complete.
        """
        try:
            makedirs(dirname(join(gitrepodir, name)))
        except OSError:
            # Directory may already exist
            pass

        with open(join(gitrepodir, name), 'w') as fh:
            fh.write(content)

        return True

    def modify_file(self, *args, **kwargs):
        """
        Alias for create_file.
        """
        return self.create_file(*args, **kwargs)

    def stage(self, gitrepodir, name, content):
        """
        Create or modify a file in a Git repository and stage it in the index.

        A ``git.Index`` object will be returned.
        """
        self.create_file(gitrepodir, name, content)

        repo = Repo(gitrepodir)
        repo.index.add([name])

        return repo.index

    def stage_remove(self, gitrepodir, name):
        """
        Stage a file for removal from the Git repository.

        Where ``name`` is the path to the file.
        """
        repo = Repo(gitrepodir)
        repo.index.remove([name])

        return repo.index

    def commit(self, gitrepodir, name, content):
        """
        Create or modify a file in a Git repository and commit it.

        A ``git.Commit`` object will be returned representing the commit.

        """
        index = self.stage(gitrepodir, name, content)

        return index.commit(name)


class ViewTestCase(JigTestCase):

    """
    Access to captured output for test cases that interact with a view.

    To use this test case, the ``setUp`` method of the sub-class must set
    ``self.view`` equal to the target view.

    """
    @property
    def output(self):
        """
        Gets any output from the view that has been collected.

        Returns an empty string if the view doesn't exist or no output has
        been collected.
        """
        if not hasattr(self, 'view'):
            return ''

        return self.view._collect['stdout'].getvalue()

    @property
    def error(self):
        """
        Gets any error messages generated by the view.

        Returns an empty string if the view doesn't exist or has no output.
        """
        if not hasattr(self, 'view'):
            return ''

        return self.view._collect['stderr'].getvalue()


class RunnerTestCase(ViewTestCase):

    """
    Test case for working with :py:class:`Runner` instances

    """
    def setUp(self):
        super(RunnerTestCase, self).setUp()

        self.runner = self._init_runner()

    def _init_runner(self):
        """
        Initialize a :py:class:`Runner` and returns it.

        This will configure the runner to collect output and not exit when it
        encounters an exceptions
        """
        runner = Runner()

        # Tell the view to collect output instead of printing it
        runner.view.collect_output = True
        # Don't exit when an exception occurs so our test can continue
        runner.view.exit_on_exception = False

        # Set this up so output() and error() can read the data
        self.view = runner.view

        return runner


class PluginTestCase(JigTestCase):

    """
    Base test case for plugin tests.

    """
    def setUp(self):
        super(PluginTestCase, self).setUp()

        # Initialize the repo and grab it's config file
        self.jigconfig = initializer(self.gitrepodir)

    def _add_plugin(self, config, plugindir):
        """
        Adds the plugin to a main jig config.
        """
        section = 'plugin:test01:{0}'.format(plugindir)
        config.add_section(section)
        config.set(section, 'path',
                   join(self.fixturesdir, plugindir))


class CommandTestCase(ViewTestCase):

    """
    Base test case for command tests.

    """
    def run_command(self, command=None):
        """
        Run a subcommand.
        """
        with patch('jig.commands.base.create_view') as cv:
            # We hijack the create_view function so we can tell it to collect
            # output and not exit on exception.
            view = ConsoleView()

            # Collect, don't print
            view.collect_output = True
            # Don't call sys.exit() on exception
            view.exit_on_exception = False

            cv.return_value = view

            # Keep a reference to this so output() and error() will work
            self.view = view

            return self.command(shlex.split(command or ''))


class FormatterTestCase(JigTestCase):

    """
    Base test case for formatters.

    """
    def run_formatter(self, results):
        """
        Creates a collator and returns formatted results.

        Subclasses must set the ``formatter`` class property to a valid
        formatter.

        :param dict results: the results to collate and format
        """
        collector = StringIO()
        collator = ResultsCollator(results)
        printer = lambda line: collector.write(unicode(line) + u'\n')

        self.formatter().print_results(printer, collator)

        return collector.getvalue()
