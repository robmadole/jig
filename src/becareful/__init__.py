import sys

from becareful.runner import Runner


def main():
    bc = Runner()
    bc.fromconsole(sys.argv)
