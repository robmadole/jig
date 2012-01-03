import argparse

from becareful.commands.base import BaseCommand
from becareful.exc import CommandError
from becareful.plugins import get_bcconfig, set_bcconfig, PluginManager

_parser = argparse.ArgumentParser(
    description='Manage BeCareful plugins',
    usage='%(prog)s plugin')

_subparsers = _parser.add_subparsers(title='actions',
    description='available commands to manage plugins')

_listparser = _subparsers.add_parser('list',
    help='list installed plugins', usage='asdf')
_listparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_listparser.set_defaults(subcommand='list')

_addparser = _subparsers.add_parser('add',
    help='add an installed plugin')
_addparser.add_argument('plugin',
    help='Path to the plugin directory')
_addparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_addparser.set_defaults(subcommand='add')

_removeparser = _subparsers.add_parser('remove',
    help='remove an installed plugin')
_removeparser.add_argument('name',
    help='Plugin name')
_removeparser.add_argument('bundle', nargs='?', default=None,
    help='Bundle name')
_removeparser.add_argument('--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_removeparser.set_defaults(subcommand='remove')


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

        return bundles;

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
            config = get_bcconfig(path)

            pm = PluginManager(config)

            bundles = self._bundles(pm)

            if not bundles:
                out.append(u'No plugins installed.')
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

    def add(self, argv):
        """
        Add a plugin.
        """
        path = argv.path
        plugin = argv.plugin

        with self.out() as out:
            config = get_bcconfig(path)

            pm = PluginManager(config)

            p = pm.add(plugin)

            set_bcconfig(path, pm.config)

            out.append('Added plugin {} in bundle {} to the repository.'.format(
                p.name, p.bundle))

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
            config = get_bcconfig(path)

            pm = PluginManager(config)

            plugins = self._plugins(pm)

            if name in plugins and not bundle:
                if len(plugins[name]) > 1:
                    # There are more than one plugin by this name
                    raise CommandError('More than one plugin has the name of '
                        '{}. Use the list command to see installed '
                        'plugins.'.format(name))

                bundle = plugins[name].bundle

            pm.remove(bundle, name)

            out.append('Removed plugin {}'.format(name))
