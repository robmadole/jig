from contextlib import contextmanager

from jig.exc import AlreadyInitialized, CIFirstRun
from jig.commands.base import BaseCommand, get_formatter
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
    '[--format FORMAT] PLUGINSFILE [PATH]')

_parser.add_argument(
    'pluginsfile',
    help='Path to a file containing the location of plugins to install, '
    'each line of the file should contain URL|URL@BRANCH|PATH')
_parser.add_argument(
    '--format', dest='output_format', default='tap', choices=['tap', 'fancy'],
    help='Output format to show results')
_parser.add_argument(
    '--tracking-branch', dest='tracking_branch', default='jig-ci-last-run',
    help='Branch name Jig will use to keep its place')
_parser.add_argument(
    'path', nargs='?', default='.',
    help='Path to the Git repository')


@contextmanager
def _when_exits_zero(call_if_ok):
    """
    Calls the function passed in if the SystemExit has a zero exit code.
    """
    try:
        yield
    except SystemExit as se:
        if getattr(se, 'code', None) == 0:
            # Update the tracking branch to reference current HEAD
            call_if_ok()
        raise


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
        self.install_plugins_file(plugins_file, path, hints=False)

        with self.out() as printer:
            # If the tracking branch is not present, create it
            # and tell the user it was the first time then exit
            tracked = Tracked(path, tracking_branch)
            if not tracked.exists:
                tracked.update(tracking_branch)

                raise CIFirstRun()

            printer(u'')
            printer(u'Tracking branch {0} references commit {1}'.format(
                tracking_branch, tracked.rev
            ))
            printer(u'')

        # Run Jig from the tracking branch to HEAD
        runner = Runner(view=self.view, formatter=get_formatter(output_format))

        with _when_exits_zero(tracked.update):
            runner.main(
                path,
                rev_range='{0}..HEAD'.format(tracking_branch),
                interactive=False
            )
