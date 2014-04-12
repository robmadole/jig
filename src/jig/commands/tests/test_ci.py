# coding=utf-8
from tempfile import mkdtemp

from jig.tests.testcase import CommandTestCase, cd_gitrepo, result_with_hint
from jig.commands.hints import AFTER_INIT
from jig.exc import ForcedExit
from jig.commands import ci


class TestInitCommand(CommandTestCase):

    """
    Test the init subcommand.

    """
    command = ci.Command
