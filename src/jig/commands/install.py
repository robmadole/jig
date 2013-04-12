import argparse

from jig.exc import PluginError
from jig.plugins import (
    get_jigconfig, set_jigconfig, PluginManager)
from jig.plugins.tools import read_plugin_list
from jig.commands.base import BaseCommand, add_plugin
from jig.commands.hints import USE_RUNNOW

_parser = argparse.ArgumentParser(
    description='Install a list of Jig plugins from a file',
    usage='jig install [-h] [-r GITREPO] [PLUGINS]')

_parser.add_argument(
    '--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_parser.add_argument(
    'plugins',
    help='Path to a file containing the location of plugins to install, '
    'each line of the file should contain URL|URL@BRANCH|PATH')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        path = argv.path
        plugins = argv.plugins

        with self.out() as out:
            try:
                plugin_list = read_plugin_list(plugins)
            except IOError as e:
                # Grab the human-readable part of the IOError and raise that
                raise PluginError(e.strerror)

            for plugin in plugin_list:
                config = get_jigconfig(path)
                pm = PluginManager(config)

                try:
                    added = add_plugin(pm, plugin, path)
                except Exception as e:
                    out.append(
                        'From {0}:\n - {1}'.format(
                            plugin, e))
                    continue

                set_jigconfig(path, pm.config)

                out.append('From {}:'.format(plugin))
                for p in added:
                    out.append(
                        ' - Added plugin {0} in bundle {1}'.format(
                            p.name, p.bundle))

            out.extend(USE_RUNNOW)
