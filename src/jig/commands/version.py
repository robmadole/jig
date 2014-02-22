import jig
from jig.commands.base import BaseCommand

try:
    import argparse
except ImportError:   # pragma: no cover
    from backports import argparse

_parser = argparse.ArgumentParser(
    description='Show Jig\'s version number',
    usage='jig version [-h]')


class Command(BaseCommand):
    parser = _parser

    def process(self, argv):
        with self.out() as out:
            out.append('{0}'.format(jig.__version__))
