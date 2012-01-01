import argparse

from becareful.commands.base import BaseCommand
from becareful.runner import Runner

_parser = argparse.ArgumentParser(
    description='Run all plugins and show the results')

_parser.add_argument('path', nargs='?', default='.',
    help='Path to the Git repository')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        path = argv.path

        # Make the runner use our view
        runner = Runner(view=self.view)

        runner.fromhook(path)
