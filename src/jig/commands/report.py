import argparse

from jig.commands.base import BaseCommand
from jig.runner import Runner

_parser = argparse.ArgumentParser(
    description='Run plugins on a revision range',
    usage='jig report [-h] [-p PLUGIN] [--rev-range REVISION_RANGE] [PATH]')

_parser.add_argument(
    '--plugin', '-p',
    help='Only run this specific named plugin')
_parser.add_argument(
    '--rev-range', dest='rev_range', default='HEAD^1..HEAD',
    help='Git revision range to run the plugins against')
_parser.add_argument(
    'path', nargs='?', default='.',
    help='Path to the Git repository')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        path = argv.path
        rev_range = argv.rev_range

        # Make the runner use our view
        runner = Runner(view=self.view)

        runner.main(
            path,
            plugin=argv.plugin,
            rev_range=rev_range,
            interactive=False
        )
