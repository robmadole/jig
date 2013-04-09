import argparse
import errno
from os.path import join
from urlparse import urlparse
from uuid import uuid4 as uuid

from jig.commands.base import BaseCommand
from jig.commands.hints import (
    NO_PLUGINS_INSTALLED, USE_RUNNOW, FORK_PROJECT_GITHUB)
from jig.conf import JIG_DIR_NAME, JIG_PLUGIN_DIR
from jig.exc import CommandError, ExpectationError
from jig.gitutils import clone
from jig.tools import indent
from jig.plugins import (get_jigconfig, set_jigconfig, PluginManager,
    create_plugin, available_templates)
from jig.plugins.tools import update_plugins
from jig.plugins.testrunner import (PluginTestRunner, PluginTestReporter,
    FailureResult, parse_range)

_parser = argparse.ArgumentParser(
    description='Manage this repository\'s Jig plugins',
    usage='jig plugin [-h] ACTION')

_subparsers = _parser.add_subparsers(title='actions',
    description='available commands to manage plugins')

_listparser = _subparsers.add_parser('list',
    help='list installed plugins',
    usage='jig plugin list [-h] [-r GITREPO] [PATH]')
_listparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_listparser.set_defaults(subcommand='list')

_addparser = _subparsers.add_parser('add',
    help='add a plugin',
    usage='jig plugin add [-h] [-r GITREPO] URL|URL@BRANCH|PATH')
_addparser.add_argument('plugin',
    help='URL or path to the plugin directory, if URL you can '
    'specify @BRANCHNAME to clone other than the default')
_addparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_addparser.set_defaults(subcommand='add')

_updateparser = _subparsers.add_parser('update',
    help='update all installed plugins',
    usage='jig plugin update [-h] [-r GITREPO]')
_updateparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_updateparser.set_defaults(subcommand='update')

_removeparser = _subparsers.add_parser('remove',
    help='remove an installed plugin',
    usage='jig plugin remove [-h] [-r GITREPO] NAME [BUNDLE]')
_removeparser.add_argument('name',
    help='Plugin name')
_removeparser.add_argument('bundle', nargs='?', default=None,
    help='Bundle name')
_removeparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_removeparser.set_defaults(subcommand='remove')

_createparser = _subparsers.add_parser('create',
    help='create a new plugin',
    usage='jig plugin create [-h] [-l] [-d] NAME BUNDLE')
_createparser.add_argument('name',
    help='Plugin name')
_createparser.add_argument('bundle',
    help='Bundle name')
_createparser.add_argument('--language', '-l', dest='template',
    default='python', help='Scripting language: {0}'.format(
        ', '.join(available_templates())))
_createparser.add_argument('--dir', '-d', default='.',
    help='Create in this directory')
_createparser.set_defaults(subcommand='create')

_testparser = _subparsers.add_parser('test',
    help='run a suite of plugin tests',
    usage='jig plugin test [-h] PLUGIN')
_testparser.add_argument('plugin', nargs='?', default='.',
    help='Path to the plugin directory')
_testparser.add_argument('--range', '-r',
    dest='range',
    help='Run a subset of the tests, specified like [s]..[e]. Example -r '
        '3..5 to run tests that have expectations for those changes.')
_testparser.add_argument('--verbose', '-v',
    default=False, action='store_true',
    help='Print the input and output (stdin and stdout)')
_testparser.set_defaults(subcommand='test')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        subcommand = argv.subcommand

        # Handle the actions
        getattr(self, subcommand)(argv)

    def _bundles(self, pm):
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

    def _plugins(self, pm):
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

    def list(self, argv):
        """
        List the installed plugins.
        """
        path = argv.path

        with self.out() as out:
            config = get_jigconfig(path)

            pm = PluginManager(config)

            bundles = self._bundles(pm)

            if not bundles:
                out.append(u'No plugins installed.')
                out.extend(NO_PLUGINS_INSTALLED)
                return

            out.append(u'Installed plugins\n')

            out.append(u'{h1:<25} {h2}'.format(
                h1=u'Plugin name', h2=u'Bundle name'))

            sort_bundles = sorted(bundles.items(), key=lambda b: b[0])

            for name, plugins in sort_bundles:
                sort_plugins = sorted(plugins, key=lambda p: p.name)

                for plugin in sort_plugins:
                    out.append(u'{plugin:.<25} {name}'.format(
                        name=name, plugin=plugin.name))

            out.extend(USE_RUNNOW)

    def add(self, argv):
        """
        Add a plugin.
        """
        path = argv.path
        plugin = argv.plugin

        with self.out() as out:
            config = get_jigconfig(path)

            pm = PluginManager(config)

            added = self._add_path_or_url(pm, plugin, path)

            set_jigconfig(path, pm.config)

            for p in added:
                out.append('Added plugin {0} in bundle {1} to the '
                    'repository.'.format(p.name, p.bundle))

            out.extend(USE_RUNNOW)

    def _add_path_or_url(self, pm, plugin, gitdir):
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

        return pm.add(plugin)

    def update(self, argv):
        """
        Updates any plugins installed through a URL.

        This basically runs ``git pull`` within any directory inside the
        :file:`.jig/plugis` directory. It's a very simple method of updating
        plugins that have already been installed.
        """
        path = argv.path

        with self.out() as out:
            # Make sure that this directory has been initialized for Jig
            get_jigconfig(path)

            results = update_plugins(path)

            if not results:
                out.append('No plugins to update.')
                return

            out.append('Updating plugins')
            out.append('')

            for pm, output in results.items():
                names = set([i.name for i in pm.plugins])
                bundles = set([i.bundle for i in pm.plugins])

                out.append('Plugin {0} in bundle {1}'.format(
                    ', '.join(names), ', '.join(bundles)))
                out.extend(indent(output.splitlines()))

    def remove(self, argv):
        """
        Remove a plugin.

        This method is smart enough to work with only the plugin name if it
        happens to be unique. If there is more than one plugin with the same
        name but in a different bundle it will exit with an error.
        """
        path = argv.path
        name = argv.name
        bundle = argv.bundle

        with self.out() as out:
            config = get_jigconfig(path)

            pm = PluginManager(config)

            plugins = self._plugins(pm)

            # Find the bundle if it's not specified
            if name in plugins and not bundle:
                if len(plugins[name]) > 1:
                    # There are more than one plugin by this name
                    raise CommandError('More than one plugin has the name of '
                        '{0}. Use the list command to see installed '
                        'plugins.'.format(name))

                bundle = plugins[name][0].bundle

            pm.remove(bundle, name)

            set_jigconfig(path, pm.config)

            out.append('Removed plugin {0}'.format(name))

    def create(self, argv):
        """
        Create a new plugin.
        """
        name = argv.name
        bundle = argv.bundle
        template = argv.template
        save_dir = argv.dir

        with self.out() as out:
            if template not in available_templates():
                raise CommandError(
                    'Language {0} is not supported yet.'.format(template),
                    hint=FORK_PROJECT_GITHUB)

            try:
                plugin_dir = create_plugin(save_dir, bundle, name,
                    template=template)

                out.append('Created plugin as {0}'.format(plugin_dir))
            except OSError as ose:
                if ose.errno == errno.EEXIST:
                    # File exists
                    raise CommandError('A plugin with this name already '
                        'exists in this directory: {0}.'.format(save_dir))
                # Something else, raise it again
                raise ose   # pragma: no cover

    def test(self, argv):
        """
        Run the tests for a plugin.
        """
        plugin = argv.plugin
        test_range = argv.range
        verbose = argv.verbose

        with self.out() as out:
            if test_range:
                test_range = parse_range(test_range)

            try:
                ptr = PluginTestRunner(plugin)

                results = ptr.run(test_range=test_range)

                reporter = PluginTestReporter(results)

                test_results = reporter.dumps(verbose=verbose).splitlines()

                failures = [i for i in results if isinstance(i, FailureResult)]

                if failures:
                    # Raise as an error so the status code will be non-zero
                    raise CommandError('\n'.join(test_results))

                # No failures, ok to send this to stdout
                out.extend(test_results)
            except ExpectationError as e:
                raise CommandError(str(e))
