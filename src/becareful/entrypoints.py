import sys


def main():
    from becareful.runner import Runner

    bc = Runner()
    bc.fromconsole(sys.argv)
