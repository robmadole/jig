from becareful.output import ConsoleView


def get_command(name):
    """
    Gets an instance of the named BeCareful sub-command.

    For example::

        >>> get_command('init')
        <becareful.commands.init.Command object at 0x10048fed0>
    """
    mod = __import__('becareful.commands.{}'.format(name.lower()),
        globals(), locals(), ['Command'], 0)
    return mod.Command


def create_view():
    """
    Creates a view the command can use to output data.

    This method is separated from the :py:class:`BaseCommand` class to
    facilitate testing. By mocking out this method, commands can use views that
    have been configured to collect output instead of sending it to the
    terminal.
    """
    return ConsoleView()


class BaseCommand(object):

    """
    Base command for implementing script sub-commands.

    """
    def __init__(self, argv):
        """
        Parse the command line arguments and call process with the results.

        Where argv is a split string. See :py:module:`shlex`.
        """
        args = self.parser.parse_args(argv)

        # Setup something our command can use to send output
        self.view = create_view()
        # A shorter alias to the view's out decorator
        self.out = self.view.out

        # Finally, process the arguments
        self.process(args)

    def process(self, args):
        """
        Perform whatever operation this command is supposed to do.
        """
        raise NotImplemented()
