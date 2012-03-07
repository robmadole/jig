import argparse

from jig.commands.base import BaseCommand
from jig.gitutils import hook
from jig.plugins import initializer

_parser = argparse.ArgumentParser(
    description='Initialize a Git repository for use with Jig',
    usage='jig init [-h] [PATH]')

_parser.add_argument('path', default='.', nargs='?',
    help='Path to the Git repository')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        path = argv.path

        with self.out() as out:
            hook(path)
            initializer(path)

            out.append('Git repository has been initialized for use '
                'with Jig.')
