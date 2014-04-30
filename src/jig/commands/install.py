from jig.exc import PluginError
from jig.plugins import (
    get_jigconfig, set_jigconfig, PluginManager)
from jig.plugins.tools import read_plugin_list
from jig.commands.base import BaseCommand, add_plugin
from jig.commands.hints import USE_RUNNOW

try:
    import argparse
except ImportError:   # pragma: no cover
    from backports import argparse

_parser = argparse.ArgumentParser(
    description='Install a list of Jig plugins from a file',
    usage='jig install [-h] [-r GITREPO] PLUGINSFILE')

_parser.add_argument(
    '--gitrepo', '-r', default='.', dest='path',
    help='Path to the Git repository, default current directory')
_parser.add_argument(
    'pluginsfile',
    help='Path to a file containing the location of plugins to install, '
    'each line of the file should contain URL|URL@BRANCH|PATH')


class InstallCommandMixin(object):

    """
    Command mixin for install-related actions.

    """
    def install_plugins_file(self, plugins_file, path, hints=True):
        with self.out() as out:
            try:
                plugin_list = read_plugin_list(plugins_file)
            except IOError as e:
                # Grab the human-readable part of the IOError and raise that
                raise PluginError(e[1])

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

                out.append('From {0}:'.format(plugin))
                for p in added:
                    out.append(
                        ' - Added plugin {0} in bundle {1}'.format(
                            p.name, p.bundle))

            if hints:
                out.extend(USE_RUNNOW)


class Command(BaseCommand, InstallCommandMixin):
    parser = _parser

    def process(self, argv):
        path = argv.path
        plugins_file = argv.pluginsfile

        self.install_plugins_file(plugins_file, path)
