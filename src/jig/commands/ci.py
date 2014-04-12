from jig.exc import AlreadyInitialized
from jig.commands.base import BaseCommand
from jig.commands.install import InstallCommandMixin
from jig.gitutils.branches import Tracked
from jig.plugins import initializer
from jig.runner import Runner

try:
    import argparse
except ImportError:   # pragma: no cover
    from backports import argparse

_parser = argparse.ArgumentParser(
    description='Run in continuous integration (CI) mode',
    usage='jig ci [-h] [--tracking-branch TRACKING_BRANCH] '
    '[--format FORMAT] PLUGINSFILE')

_parser.add_argument(
    'pluginsfile',
    help='Path to a file containing the location of plugins to install, '
    'each line of the file should contain URL|URL@BRANCH|PATH')
_parser.add_argument(
    '--format', dest='output_format', default='tap', choices=['tap', 'jig'],
    help='Output format to show results')
_parser.add_argument(
    '--tracking-branch', dest='tracking_branch', default='jig-ci-last-run',
    help='Branch name Jig will use to keep its place')
_parser.add_argument(
    'path', nargs='?', default='.',
    help='Path to the Git repository')


class Command(BaseCommand, InstallCommandMixin):
    parser = _parser

    def process(self, argv):
        path = argv.path
        plugins_file = argv.pluginsfile
        tracking_branch = argv.tracking_branch
        output_format = argv.output_format

        # Make sure that the Git directory has been initialized
        try:
            initializer(path)
        except AlreadyInitialized:
            # This is OK since this command will run repeatedly in CI mode
            pass

        # Make sure the plugins are installed
        self.install_plugins_file(plugins_file)

        with self.out() as out:
            # If the tracking branch is not present, create it
            # and tell the user it was the first time then exit
            tracked = Tracked(path, tracking_branch)
            if not tracked.exists():
                tracked.update(tracking_branch)

                out.append('First run, tracking branch created for HEAD')
            else:
                # Run Jig from the tracking branch to HEAD

                # Update the tracking branch to reference current HEAD
                tracked.update('HEAD')
