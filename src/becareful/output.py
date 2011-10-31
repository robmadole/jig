import sys
from StringIO import StringIO
from contextlib import contextmanager

from becareful.exc import RunnerExit


class View(object):

    """
    Base View all other sub views inherit from.

    """
    pass


class ConsoleView(View):

    """
    Main view used to handle output to the console.

    """
    def __init__(self):
        # Do we collect output? False means we print it out
        self.collect_output = False
        self.exit_on_exception = True
        self._collect = {
            'stdout': StringIO(), 'stderr': StringIO()}

    @contextmanager
    def out(self):
        collected = []

        try:
            yield collected

            fo = self._collect['stdout'] if self.collect_output else sys.stdout

            for line in collected:
                fo.write(str(line))
        except Exception as e:
            fo = self._collect['stderr'] if self.collect_output else sys.stderr
            fo.write(str(e))

            try:
                retcode = e.retcode
            except AttributeError:
                # This exception does not have a return code, assume 1
                retcode = 1

            if self.exit_on_exception:
                sys.exit(retcode)
            else:
                raise RunnerExit(retcode)
