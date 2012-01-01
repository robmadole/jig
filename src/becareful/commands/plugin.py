import argparse

from becareful.commands.base import BaseCommand
from becareful.plugins import get_bcconfig, PluginManager

_parser = argparse.ArgumentParser(
    description='Manage BeCareful plugins',
    usage='%(prog)s plugin [action] [options]')

_subparsers = _parser.add_subparsers(title='actions',
    description='available commands to manage plugins')

_listparser = _subparsers.add_parser('list',
    help='list installed plugins')
_listparser.add_argument('path', nargs='?', default='.',
    help='Path to the Git repository')
_listparser.set_defaults(subcommand='list')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        subcommand = argv.subcommand

        # Handle the actions
        getattr(self, subcommand)(argv)

    def list(self, argv):
        """
        List the installed plugins.
        """
        path = argv.path

        with self.out() as out:
            config = get_bcconfig(path)

            pm = PluginManager(config)

            bundles = {}

            for plugin in pm.plugins:
                if plugin.bundle not in bundles:
                    bundles[plugin.bundle] = []
                bundles[plugin.bundle].append(plugin)

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
