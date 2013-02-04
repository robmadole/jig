import sys


def main():
    """
    Main jig command line tool.

    Provides access to all the jig user commands.
    """
    from jig.runner import Runner

    jig = Runner()
    jig.fromconsole(sys.argv)


def test():
    """
    Run the suite of tests for jig.
    """
    import nose

    from jig.tests.noseplugin import TestSetup

    nose.main(argv=['nose', '-w', 'src'] + sys.argv[1:],
            addplugins=[TestSetup()])


def coverage():
    """
    Create console and HTML coverage reports for the full test suite.
    """
    from coverage import coverage
    import nose

    cov = coverage(branch=True, config_file=False, source=['jig'],
        omit=['*noseplugin*', '*entrypoints*', '*testcase*'])

    cov.start()

    nose.run(argv=['nose'])

    cov.stop()

    cov.report()
    cov.html_report(directory='cover')
