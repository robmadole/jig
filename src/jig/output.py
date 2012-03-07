import sys
from functools import wraps
from StringIO import StringIO
from contextlib import contextmanager

from jig.exc import ForcedExit

# Message types
INFO = u'info'
WARN = u'warn'
STOP = u'stop'


def green_bold(payload):
    """
    Format payload as green.
    """
    return u'\x1b[32;1m{}\x1b[39;22m'.format(payload)


def yellow_bold(payload):
    """
    Format payload as yellow.
    """
    return u'\x1b[33;1m{}\x1b[39;22m'.format(payload)


def red_bold(payload):
    """
    Format payload as red.
    """
    return u'\x1b[31;1m{}\x1b[39;22m'.format(payload)


def strip_paint(payload):
    """
    Removes any console specific color characters.

    Where ``payload`` is a string containing special characters used to print
    colored output to the terminal.

    Returns a unicode string without the paint.
    """
    strip = [u'\x1b[31;1m', u'\x1b[32;1m', u'\x1b[33;1m', u'\x1b[39;22m']
    for paint in strip:
        payload = payload.replace(paint, '')
    return payload


def lookup_type(strtype):
    """
    Returns the actual type for a string message representation of it.

    For example::

        >>> lookup_type('Info')
        u'info'
        >>> lookup_type('warn')
        u'warn'
        >>> lookup_type('s')
        u'stop'

    It will default to ``INFO``.

        >>> lookup_type('unknown'):
        u'info'

    """
    strtype = unicode(strtype) or u''
    mt = strtype.lower()
    if mt.startswith(u'i'):
        return INFO
    if mt.startswith(u'w'):
        return WARN
    if mt.startswith(u's'):
        return STOP

    # Default to INFO
    return INFO


class Message(object):

    """
    Represents one message that a plugin is communicating to the user.

    """
    def __init__(self, plugin, type=INFO, body='', file=None, line=None):
        """
        Create a message object associated with a plugin.

        All messages must be associated with the Plugin ``plugin`` that was
        responsible for creating them.
        """
        self.plugin = plugin

        self.type = type
        self.body = body
        self.file = file
        self.line = line

    def __repr__(self):
        reprstr = '<{cls} type="{t}", body={b}, file={f}, line={l}>'
        return reprstr.format(cls=self.__class__.__name__,
            t=self.type, b=repr(self.body), f=repr(self.file), l=self.line)

    def __eq__(self, other):
        """
        If type, body, file, and line attributes are the same they are equal.
        """
        try:
            attrs = ('type', 'body', 'file', 'line')
            for attr in attrs:
                if not getattr(self, attr) == getattr(other, attr):
                    return False
        except AttributeError:
            # If the other object is missing an attribute they can't be equal.
            return False
        return True

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = lookup_type(value)


class Error(Message):

    """
    An error message related to a plugin's results.

    """
    def __init__(self, *args, **kwargs):
        if 'type' not in kwargs:
            # Default to stop for errors
            kwargs['type'] = 'stop'

        super(Error, self).__init__(*args, **kwargs)


class ConsoleView(object):

    """
    Main view used to handle output to the console.

    """
    def __init__(self, collect_output=False, exit_on_exception=True,
            stdout=None, stderr=None):
        # Do we collect output? False means we print it out
        self.collect_output = collect_output
        self.exit_on_exception = exit_on_exception
        self._collect = {
            'stdout': stdout or StringIO(), 'stderr': stderr or StringIO()}

    @contextmanager
    def out(self):
        collected = []

        try:
            yield collected

            fo = self._collect['stdout'] if self.collect_output else sys.stdout

            for line in collected:
                fo.write(unicode(line) + u'\n')
        except Exception as e:
            fo = self._collect['stderr'] if self.collect_output else sys.stderr
            fo.write(unicode(e) + u'\n')

            try:
                retcode = e.retcode
            except AttributeError:
                # This exception does not have a return code, assume 1
                retcode = 1

            if self.exit_on_exception:
                sys.exit(retcode)   # pragma: no cover
            else:
                raise ForcedExit(retcode)

    def print_results(self, results):
        """
        Format and print plugins results.
        """
        if not results:
            return

        collater = ResultsCollater(results)

        plugins = collater.plugins
        errors = collater.errors
        reporters = collater.reporters

        form = u'plugin' if len(plugins) == 1 else u'plugins'

        if len(reporters) == 0 and len(errors) == 0:
            # Nothing to report
            with self.out() as out:
                form = u'plugin' if len(plugins) == 1 else u'plugins'
                out.append(u'Ran {plen} {form}, nothing to report'.format(
                    plen=len(plugins), form=form))
                return

        # Gather the distinct message types from the results
        cm, fm, lm = collater.messages

        # Order them from least specific to most specific, put the errors last
        messages = cm + fm + lm + errors

        # How do our message types map to a symbol
        type_to_symbol = {
            INFO: green_bold(u'\u2713'),
            WARN: yellow_bold(u'\u26a0'),
            STOP: red_bold(u'\u2715')}

        ic, wc, sc = (0, 0, 0)
        with self.out() as out:
            last_plugin = None
            for msg in messages:
                if last_plugin != msg.plugin:
                    out.append(u'\u25be  {}'.format(msg.plugin.name))
                    out.append('')
                    last_plugin = msg.plugin
                colorized = u'{}  {}'.format(
                    type_to_symbol[msg.type], self._format_message(msg))
                out.extend(colorized.splitlines())
                out.append('')

            out.append(u'Ran {plen} {form}'.format(
                plen=len(plugins), form=form))

            ic, wc, sc = [i[1] for i in collater.counts.items()]
            info = green_bold(ic) if ic else ic
            warn = yellow_bold(wc) if wc else wc
            stop = red_bold(sc) if sc else sc

            out.append(u'    Info {ic} Warn {wc} Stop {sc}'.format(
                ic=info, wc=warn, sc=stop))

            if len(errors):
                out.append(u'    ({ec} {form} reported errors)'.format(
                    ec=len(errors), form=form))

        # Return the counts for the different types of messages
        return (ic, wc, sc)

    def print_help(self, commands):
        """
        Format and print help for using the console script.
        """
        with self.out() as out:
            out.append('usage: jig [-h] COMMAND')
            out.append('')

            out.append('optional arguments:')
            out.append('  -h, --help  show this help message and exit')
            out.append('')

            out.append('jig commands:')
            for command in commands:
                name = command.__module__.split('.')[-1]
                description = command.parser.description

                out.append('  {name:12}{description}'.format(
                    name=name, description=description))

            out.append('')
            out.append('See `jig COMMAND --help` for more information')

    def _format_message(self, msg):
        """
        Formats a single message to a string.
        """
        out = []
        header = u''
        body = u''

        if msg.line:
            header += u'line {}: '.format(msg.line)

        if msg.file:
            header += msg.file

        if header:
            body = u'    {}'.format(msg.body)
        else:
            body = u'{}'.format(msg.body)

        if header:
            out.append(header)

        out.append(body)

        return '\n'.join(out)


class ResultsCollater(object):

    """
    Collects and combines plugin results into a unified summary.

    """
    def __init__(self, results):
        # Decorate our message methods
        setattr(self, '_commit_specific_message',
            self.iterresults(self._commit_specific_message))
        setattr(self, '_file_specific_message',
            self.iterresults(self._file_specific_message))
        setattr(self, '_line_specific_message',
            self.iterresults(self._line_specific_message))

        self._results = results
        self._plugins = set()
        self._reporters = set()
        self._counts = {INFO: 0, WARN: 0, STOP: 0}
        self._errors = []

        # Pre-compute our messages (collate)
        self._cm = list(self._commit_specific_message())
        self._fm = list(self._file_specific_message())
        self._lm = list(self._line_specific_message())

    @property
    def messages(self):
        """
        Messages by type for the plugin results.

        Return a tuple of messages by type based on the results that were
        provided when initializing the collater.

        Each tuple contains a generator object which will return
        ``jig.output.Message`` objects.

        The tuple has a length of 3 and is in this order:

            1. Commit specific messages
            2. File specific messages
            3. Line specific messages
        """
        return (self._cm, self._fm, self._lm)

    @property
    def plugins(self):
        """
        Provides a set of plugins that were present in the results.

        This method will return a plugin regardless of whether it yielded
        messages or not.
        """
        return self._plugins

    @property
    def reporters(self):
        """
        Provides a set of plugins that yielded messages.

        This method will only provide something other than an empty set when
        the commit, file, or line specific message methods have been called.
        """
        return self._reporters

    @property
    def counts(self):
        """
        Tally of the type of messages from the results.

        Returns a dictionary like::

            {u'info': 5, u'warn': 0, u'stop', 1}
        """
        return self._counts

    @property
    def errors(self):
        """
        Errors that were generated during collation.

        Errors are found when a piece of data given to one of the collaters is
        of a type that can't be understood.

        Returns a list of ``jig.output.Error`` objects.
        """
        return self._errors

    def iterresults(self, func):
        """
        Decorator that iterates through results.

        This simplifies some of the boilerplate for our collation. The
        decorated function must be a generator that yields ``Message`` or
        ``Error`` object. It will sift errors and collect those into a separate
        container. The ``Message`` objects then be returned to the caller.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            for plugin, result in self._results.items():
                self._plugins.add(plugin)

                retcode, stdout, stderr = result

                if not retcode == 0:
                    error = Error(plugin)
                    error.body = stderr
                    self._errors.append(error)
                    # Remove this plugin since it's an error. If we don't do
                    # this we'll end up reporting on this 3 times.
                    del self._results[plugin]
                    continue

                for message in list(func(plugin, stdout)):
                    if isinstance(message, Error):
                        self._errors.append(message)
                        try:
                            del self._results[plugin]
                        except KeyError:
                            pass
                        continue   # pragma: no cover
                    self._reporters.add(plugin)
                    self._counts[message.type] += 1
                    yield message

        return wrapper

    def _commit_specific_message(self, plugin, obj):
        """
        Look for plugins that are reporting generic messages.

        These messages are not specific to any file or line number. They
        generally come from plugins that are inspecting the commit as a whole
        and reporting on some characteristic. A good example of this would be a
        plugin that checked to see if any modifications were made to a docs
        directory if modifications were also made to a src directory.
        Basically, a "did you write/update the docs" message.
        """
        if not obj:
            # This is falsy, there is nothing of interest here
            return

        if isinstance(obj, dict):
            # This is for file or line specific messages
            return

        if isinstance(obj, basestring):
            # Straight up message, normalize this for our loop
            obj = [obj]

        if isinstance(obj, list):
            # It's a list of [TYPE, BODY]
            for m in obj:
                if not m:
                    continue
                if isinstance(m, basestring):
                    # Straight up message, normalize this for our loop
                    yield Message(plugin, body=m)
                    continue
                if not isinstance(m, list) or len(m) != 2:
                    yield Error(plugin, body=m)
                    continue
                if not m[1]:
                    # Empty message body, this isn't useful
                    continue
                yield Message(plugin, type=m[0], body=m[1])
            # We understood this, so no need to continue
            return

        # This object is not understood
        yield Error(plugin, body=obj)

    def _file_specific_message(self, plugin, obj):
        """
        Look for plugins that are reporting file specific messages.

        These messages are specific to a file but not necessarily to a line
        number. In general they apply to a condition that is present that
        affects the whole file. An example of this would be detecting
        underscores or camel case in the filename.
        """
        if not isinstance(obj, dict):
            # This is not a file specific messages
            return

        for filename, group in obj.items():
            if isinstance(group, basestring):
                group = [group]

            if not isinstance(group, list):
                yield Error(plugin, body=group, file=filename)
                continue

            for msg in group:
                if isinstance(msg, basestring):
                    msg = [msg]

                if not isinstance(msg, list):
                    yield Error(plugin, body=msg, file=filename)
                    continue
                if len(msg) == 0:
                    # There is nothing here of interest
                    continue
                if len(msg) == 1:
                    # Should default to info type
                    if not msg[0]:
                        continue
                    yield Message(plugin, body=msg[0], file=filename)
                    continue
                if len(msg) == 2:
                    if not msg[1]:
                        continue
                    # In the format of [TYPE, BODY]
                    yield Message(plugin, body=msg[1], type=msg[0],
                        file=filename)
                    continue
                if len(msg) == 3:
                    if not msg[2]:
                        continue
                    # In the format of [LINE, TYPE, BODY]
                    if msg[0] is not None:
                        # This is line specific, skip this
                        continue
                    yield Message(plugin, body=msg[2], type=msg[1],
                        file=filename)
                    continue

                # This object is not understood
                yield Error(plugin, body=obj)

    def _line_specific_message(self, plugin, obj):
        """
        Look for plugins that are reporting line specific messages.

        For plugins wishing to identify specific lines, they use line specific
        messages. For example, you may have a JavaScript plugin that reports
        the existence of ``console.log`` on line 45. This allows the developer
        to pinpoint the problem much quicker than file or commit specific
        messages.

        There is a lack of error handling in this method. The commit and file
        specific handlers take care of error handling for us. This method gets
        to be pretty clean.
        """
        if not isinstance(obj, dict):
            # This is not a file or line specific messages
            return

        for filename, group in obj.items():
            if isinstance(group, basestring):
                group = [group]

            for msg in group:
                if isinstance(msg, basestring):
                    msg = [msg]

                if 0 <= len(msg) <= 2:
                    # There is nothing here of interest
                    continue

                if msg[0] is None:
                    # This is not line specific
                    continue
                if not msg[2]:
                    # The body is empty
                    continue
                # In the format of [LINE, TYPE, BODY]
                yield Message(plugin, body=msg[2], type=msg[1],
                    file=filename, line=msg[0])
                continue
