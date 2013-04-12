from urlparse import urlparse
from os import listdir
from os.path import join, dirname, isdir
from shutil import rmtree
from uuid import uuid4 as uuid

from jig.exc import PluginError
from jig.conf import JIG_DIR_NAME, JIG_PLUGIN_DIR
from jig.output import ConsoleView
from jig.gitutils import clone

_commands_dir = dirname(__file__)


def list_commands():
    """
    List the commands available.
    """
    commands = []
    for f in listdir(_commands_dir):
        if isdir(join(_commands_dir, f)):
            continue
        if not f.endswith('.py'):
            continue
        try:
            commands.append(get_command(f.split('.')[0]))
        except (ImportError, AttributeError):
            continue
    return commands


def get_command(name):
    """
    Gets an instance of the named jig sub-command.

    For example::

        >>> get_command('init')
        <jig.commands.init.Command object at 0x10048fed0>
    """
    mod = __import__(
        'jig.commands.{0}'.format(name.lower()),
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


def add_plugin(pm, plugin, gitdir):
    """
    Adds a plugin by filename or URL.

    Where ``pm`` is an instance of :py:class:`PluginManager` and ``plugin``
    is either the URL to a Git Jig plugin repository or the file name of a
    Jig plugin. The ``gitdir`` is the path to the Git repository which will
    be used to find the :file:`.jig/plugins` directory.
    """
    # If this looks like a URL we will clone it first
    url = urlparse(plugin)

    if url.scheme:
        # This is a URL, let's clone it first into .jig/plugins
        # directory.
        plugin_parts = plugin.rsplit('@', 1)

        branch = None
        try:
            branch = plugin_parts[1]
        except IndexError:
            pass

        to_dir = join(gitdir, JIG_DIR_NAME, JIG_PLUGIN_DIR, uuid().hex)
        clone(plugin_parts[0], to_dir, branch)
        plugin = to_dir

    try:
        return pm.add(plugin)
    except PluginError:
        # Clean-up the cloned directory becuase this wasn't installed correctly
        if url.scheme:
            rmtree(plugin)

        raise


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
        raise NotImplementedError
