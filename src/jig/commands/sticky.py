from jig.commands.base import BaseCommand
from jig.gitutils.hooking import (
    create_auto_init_templates, set_templates_directory)

try:
    import argparse
except ImportError:
    from backports import argparse

_parser = argparse.ArgumentParser(
    description='Make Jig auto-init every time you git clone',
    usage='jig sticky [-h]')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        with self.out() as out:
            templates_directory = create_auto_init_templates()

            set_templates_directory(templates_directory)

            out.append('Jig has been setup to run everytime you clone.')
