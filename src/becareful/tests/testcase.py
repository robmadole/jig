import shlex
import unittest
from subprocess import check_output, STDOUT, CalledProcessError

from becareful.runner import Runner


class BeCarefulTestCase(unittest.TestCase):

    """
    Base test case for all BeCareful tests.

    """
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


class RunnerTestCase(BeCarefulTestCase):

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

        return runner

    @property
    def output(self):
        """
        Gets any output from the view that has been collected.

        Returns an empty string if the runner doesn't exist or no output has
        been collected.
        """
        if not hasattr(self, 'runner'):
            return ''

        return self.runner.view._collect['stdout'].getvalue()

    @property
    def error(self):
        """
        Gets any error messages generated by the view.

        Returns an empty string if the runner doesn't exist or has no output.
        """
        if not hasattr(self, 'runner'):
            return ''

        return self.runner.view._collect['stderr'].getvalue()
