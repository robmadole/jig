import sys
import traceback
from urlparse import urlparse
from os import listdir
from os.path import join, dirname, isdir
from tempfile import mkstemp
from shutil import rmtree
from uuid import uuid4 as uuid
from textwrap import dedent

from jig.exc import PluginError, ForcedExit
from jig.conf import JIG_DIR_NAME, JIG_PLUGIN_DIR
from jig.output import ConsoleView
from jig.formatters import tap, fancy
from jig.gitutils.remote import clone

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


def get_formatter(name, default=fancy.FancyFormatter):
    """
    Get a formatter class suitable for formatting Jig results.

    :param str name: the short name of the formatter
    :param class default: the default formatter to return if a bad name is given
    :rtype: Formatter
    """
    formatter_classes = [
        tap.TapFormatter,
        fancy.FancyFormatter
    ]

    for cls in formatter_classes:
        if cls.name == name:
            return cls

    return default


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


def plugins_by_bundle(pm):
    """
    Organize plugins by bundle name.

    Returns a dict where the key is the bundle name and the value is a list
    of all plugins that are part of that bundle.
    """
    bundles = {}

    for plugin in pm.plugins:
        if plugin.bundle not in bundles:
            bundles[plugin.bundle] = []
        bundles[plugin.bundle].append(plugin)

    return bundles


def plugins_by_name(pm):
    """
    Organize plugins by plugin name.

    Returns a dict where the key is the plugin name and the value is a list
    of all plugins that have that name.
    """
    plugins = {}

    for plugin in pm.plugins:
        if plugin.name not in plugins:
            plugins[plugin.name] = []
        plugins[plugin.name].append(plugin)

    return plugins


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
        try:
            self.process(args)
        except (NotImplementedError, SystemExit, ForcedExit):
            raise
        except Exception as e:
            # Uncaught exception, usually means there is a bug in Jig
            self.crash_report(e, args)
            sys.exit(2)

    def process(self, args):
        """
        Perform whatever operation this command is supposed to do.
        """
        raise NotImplementedError

    def crash_report(self, exception, args):
        """
        Create a crash report and ask the user to create a GitHub issue.

        :param Exception exception: some uncaught exception
        :param ArgumentParser args: original arguments for the command.
        """
        fd, report_file = mkstemp(suffix='.jigcrash')

        exc_info = sys.exc_info()

        report_contents = dedent(u"""
            Arguments:

            {args}

            Traceback:

            {traceback}
            """
        ).strip().format(
            args=str(args),
            traceback=u''.join(traceback.format_exception(*exc_info))
        )

        with open(report_file, 'w') as fh:
            fh.write(report_contents + '\n')

        message = dedent(u"""
            --- CRASH REPORT ---

            Jig has failed to operate as expected.

            A crash report has been created: {report_file}

            Please visit http://github.com/robmadole/jig/issues and file
            an Issue and use the contents of this crash report in the description.

            --- CRASH REPORT ---
            """
        ).strip().format(
            report_file=report_file
        )

        sys.stderr.write(message + '\n')
