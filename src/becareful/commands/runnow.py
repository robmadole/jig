import argparse

from becareful.commands.base import BaseCommand
from becareful.runner import Runner

_parser = argparse.ArgumentParser(
    description='Run all plugins and show the results')

_parser.add_argument('path', default='.', help='Path the Git repository')


class Command(BaseCommand):

    """
    Performs the same actions as the pre-commit hook, without committing

    """
    parser = _parser

    def process(self, argv):
        path = argv.path

        # Make the runner use our view
        runner = Runner(view=self.view)

        runner.fromhook(path)
