# coding=utf-8
import sys

from mock import Mock, patch

from jig.entrypoints import main
from jig.tests.testcase import ViewTestCase, CommandTestCase
from jig.commands.base import list_commands, create_view, BaseCommand


class TestCommands(ViewTestCase):

    """
    Test the main parts of the command-line utility.

    """

    help_output = '''
        usage: jig [-h] COMMAND

        optional arguments:
          -h, --help  show this help message and exit

        jig commands:
          init        Initialize a Git repository for use with jig
          plugin      Manage jig plugins
          runnow      Run all plugins and show the results

        See `jig COMMAND --help` for more information'''

    def setUp(self):
        self.view = create_view()

        self.view.collect_output = True
        self.view.exit_on_exception = False

    def test_main(self):
        with patch.object(sys, 'stdout') as p:
            main()

        output = ''
        for stdout_call in p.write.call_args_list:
            output += stdout_call[0][0]

        self.assertResults(self.help_output, output)

    def test_main_help(self):
        """
        Will provide help menu when ran with no arguments.
        """
        commands = list_commands()

        self.view.print_help(commands)

        self.assertResults(self.help_output, self.output)


class TestBaseCommand(CommandTestCase):

    """
    Test our base command class.

    """
    def test_abstract_process(self):
        """
        The process method is abstract.
        """
        class MissingProcessCommand(BaseCommand):
            parser = Mock()

        with self.assertRaises(NotImplementedError):
            MissingProcessCommand([])
