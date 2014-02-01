# coding=utf-8
from tempfile import mkdtemp

import jig
from jig.tests.testcase import CommandTestCase
from jig.commands import version


class TestVersionCommand(CommandTestCase):

    """
    Test the version subcommand.

    """
    command = version.Command

    def test_shows_version(self):
        """
        Shows Jig's current version.
        """
        self.run_command()

        self.assertResults(
            '{0}'.format(jig.__version__),
            self.output)
