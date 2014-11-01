from jig.commands.base import BaseCommand
from jig.commands.hints import AFTER_INIT
from jig.gitutils.hooking import hook
from jig.plugins import initializer

try:
    import argparse
except ImportError:   # pragma: no cover
    from backports import argparse

_parser = argparse.ArgumentParser(
    description='Initialize a Git repository for use with Jig',
    usage='jig init [-h] [PATH]')

_parser.add_argument(
    'path', default='.', nargs='?',
    help='Path to the Git repository')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        path = argv.path

        with self.out() as printer:
            hook(path)
            initializer(path)

            printer(
                'Git repository has been initialized for use with Jig.'
            )
            printer(AFTER_INIT)
