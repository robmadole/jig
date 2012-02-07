import sys


def main():
    """
    Main becareful command line tool.

    Provides access to all the BeCareful user commands.
    """
    from becareful.runner import Runner

    bc = Runner()
    bc.fromconsole(sys.argv)


def test():
    """
    Run the suite of tests for BeCareful.
    """
    import nose

    nose.main(argv=['nose'] + sys.argv[1:])


def coverage():
    """
    Create console and HTML coverage reports for the full test suite.
    """
    from coverage import coverage
    import nose

    cov = coverage(branch=True, config_file=False, source=['becareful'],
        omit=['*noseplugin*', '*entrypoints*', '*testcase*'])

    cov.start()

    nose.run(argv=['nose'])

    cov.stop()

    cov.report()
    cov.html_report()
