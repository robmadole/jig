# coding=utf-8
import json
import re
from codecs import open
from os.path import join, abspath
from StringIO import StringIO
from collections import namedtuple
from operator import itemgetter
from ConfigParser import SafeConfigParser

from docutils import nodes, core, io
from docutils.parsers.rst import Directive, directives

from jig.exc import (ExpectationNoTests, ExpectationFileNotFound,
    ExpectationParsingError, RangeError)
from jig.conf import (CODEC, PLUGIN_EXPECTATIONS_FILENAME,
    PLUGIN_TESTS_DIRECTORY)
from jig.tools import NumberedDirectoriesToGit, cwd_bounce, indent
from jig.diffconvert import describe_diff
from jig.output import ConsoleView, strip_paint, green_bold, red_bold
from jig.plugins import PluginManager
from jig.plugins.manager import PluginDataJSONEncoder
from jig.diffconvert import GitDiffIndex

try:
    from collections import OrderedDict
except ImportError:   # pragma: no cover
    from ordereddict import OrderedDict

# What docutil nodes signify a structural or sectional break
DOCUTILS_DIFFERENT_SECTION_NODES = (nodes.Root, nodes.Structural,
    nodes.Titular)

# How wide do we want the columns to be when we report test output
REPORTER_COLUMN_WIDTH = 80
# A horizontal dividing line to separate sections
REPORTER_HORIZONTAL_DIVIDER = u''.join([u'·'] * REPORTER_COLUMN_WIDTH)

RESULTS_SUMMARY_SIGNATURE_RE = re.compile(
    r'^.*Jig\ ran.*$', re.MULTILINE)
RESULTS_SUMMARY_COUNT_RE = re.compile(
    r'^.*Info\ \d*\ Warn\ \d*\ Stop\ \d*$', re.MULTILINE)

# Valid test ranges will match this
RANGE_RE = re.compile(
    r'^(\d+)\.\.(\d+)$')


def get_expectations(input_string):
    """
    Converts a .rst document into a list of :py:class:`Expectation`.

    Expectation can be expressed in single reStructuredText documents that
    serve as documentation for the plugin and also as the tests.

    The :py:class:`PluginTestRunner` understands :py:class:`Expectation`
    objects and will run the plugin to assert that a plugin behaves as the
    expectation describes.

    A couple of custom directives allow the expectation to be expressed like
    this ::

        Will check a filename
        =====================

        The filename checker plugin will look at new files being added to a
        repository and make sure they follow a simple set of rules.

        .. plugin-settings::

            message_type = warn
            underscore_in_filenames = false
            capital_letters_in_filenames = false

        These settings will not allow underscores or capital letters in
        filenames. The ``message_type`` is set to ``warn`` which will notify
        the user that problems occur but will not prevent them from being
        committed.

        .. expectation::
           :from: 01
           :to: 02

            ▾  File name checker

            ✓  New file looks OK (matches filename rules)

            Ran 1 plugin
                Info 1 Warn 0 Stop 0
    """
    warning_stream = StringIO()
    overrides = {
        'input_encodings': 'unicode',
        'warning_stream': warning_stream}

    output, pub = core.publish_programmatically(
        source_class=io.StringInput, source=input_string,
        source_path=None,
        destination_class=io.NullOutput, destination=None,
        destination_path=None,
        reader=None, reader_name='standalone',
        parser=None, parser_name='restructuredtext',
        writer=None, writer_name='null',
        settings=None, settings_spec=None,
        settings_overrides=overrides,
        config_section=None, enable_exit_status=None)

    if warning_stream.getvalue():
        raise ExpectationParsingError(warning_stream.getvalue())

    flat_nodes = pub.writer.document.traverse()
    for i, node in enumerate(flat_nodes):
        if isinstance(node, expectations_node):
            # We have an expectation
            expectation = node
            settings = None

            # Hunt for settings
            for hunt_i in range(i - 1, 0, -1):   # pragma: no branch
                contender = flat_nodes[hunt_i]
                if isinstance(contender, plugin_settings_node):
                    # We found a plugin setting in the same area as the
                    # expectation, let's use this.
                    settings = contender.settings
                    break
                if isinstance(contender, DOCUTILS_DIFFERENT_SECTION_NODES):
                    # This is a structural element, anything past this is in a
                    # different section so we will stop.
                    break

            yield Expectation(range=expectation.range, settings=settings,
                    output=expectation.rawsource)


def parse_range(range_string):
    """
    Takes a range specified as a string and converts it to a list of tuples.

    Example:

        >>> parse_range('2..6')
        [(2, 3), (3, 4), (4, 5), (5, 6)]

    :param str range_string: like ``3..4`` or ``1..5``
    :rtype list:
    """
    match = RANGE_RE.match(range_string)

    if not match:
        raise RangeError(
            '{} is an invalid numbered test range'.format(
                range_string))

    start, end = match.groups()

    if not start < end:
        raise RangeError(
            '{} must be less than {} to be valid'.format(
                start, end))

    parsed_range = []

    for i in range(int(start), int(end)):
        parsed_range.append((i, i + 1))

    return parsed_range


class Result(tuple):

    """
    Result(expectation, actual, plugin, stdin, stdout)

    """
    __slots__ = ()

    _fields = ('expectation', 'actual', 'plugin', 'stdin', 'stdout')

    def __new__(_cls, expectation, actual, plugin, stdin='', stdout=''):
        return tuple.__new__(_cls, (
            expectation, actual, plugin, stdin, stdout))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        """
        Make a new Result object from a sequence or iterable.
        """
        result = new(cls, iterable)
        if len(result) != 5:
            raise TypeError('Expected 5 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        """
        Return a nicely formatted representation string.
        """
        reprformat = 'Result(expectation=%r, actual=%r, plugin=%r, ' + \
            'stdin=%r, stdout=%r)'
        return reprformat % self

    def _asdict(self):
        """
        Return a new OrderedDict which maps field names to their values.
        """
        return OrderedDict(zip(self._fields, self))

    def _replace(_self, **kwds):
        """
        Return a new object replacing specified fields with new values.
        """
        result = _self._make(map(kwds.pop,
            ('expectation', 'actual', 'plugin', 'stdin', 'stdout'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        """
        Return self as a plain tuple.  Used by copy and pickle.
        """
        return tuple(self)

    expectation = property(itemgetter(0), doc='Alias for field number 0')
    actual = property(itemgetter(1), doc='Alias for field number 1')
    plugin = property(itemgetter(2), doc='Alias for field number 2')
    stdin = property(itemgetter(3), doc='Alias for field number 3')
    stdout = property(itemgetter(4), doc='Alias for field number 4')


class SuccessResult(Result):

    """
    The expectation for a single plugins tests matched its output.

    """
    def __repr__(self):   # pragma: no cover
        return '<SuccessResult from={0} to={1}>'.format(*self.expectation.range)


class FailureResult(Result):

    """
    The expectation for a single plugins tests does not match its output.

    """
    def __repr__(self):   # pragma: no cover
        return '<FailureResult from={0} to={1}>'.format(*self.expectation.range)


class InstrumentedGitDiffIndex(GitDiffIndex):

    """
    A GitDiffIndex that can be specially instrumented for testing.

    """
    def __init__(self, gitrepo, difflist):
        super(InstrumentedGitDiffIndex, self).__init__(gitrepo, difflist)

        # Allows filepaths to be modified on the fly when the
        # :py:method:`files()` method is called.
        # This should be a tuple of (REAL_PATH, REPLACEMENT_PATH)
        self.replace_path = (None, None)

    def files(self):
        real_files = super(InstrumentedGitDiffIndex, self).files()

        for f in real_files:
            if all(self.replace_path):
                f['filename'] = f['filename'].replace(
                    self.replace_path[0], self.replace_path[1])
            yield f


class PluginTestRunner(object):

    """
    Run tests to verify a plugin functions as expected.

    """
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.timeline = None
        self.expectations = None

        try:
            test_directory = join(plugin_dir, PLUGIN_TESTS_DIRECTORY)
            self.timeline = NumberedDirectoriesToGit(test_directory)
        except ValueError:
            raise ExpectationNoTests('Could not find any tests: {0}.'.format(
                test_directory))

        try:
            expect_filename = join(plugin_dir, PLUGIN_TESTS_DIRECTORY,
                PLUGIN_EXPECTATIONS_FILENAME)

            with open(expect_filename, 'r', CODEC) as fh:
                expectation_text = fh.read()   # pragma: no branch

            self.expectations = list(get_expectations(expectation_text))
        except (IOError, OSError):
            raise ExpectationFileNotFound(
                'Missing expectation file: {0}.'.format(expect_filename))

    def run(self, test_range=None):
        """
        Run the tests for this plugin.

        Returns a list of :py:class:`Result` objects which represent the
        results from the test run.

        :param list test_range: None or the parsed range from :function:`parse_range`
        """
        # Use an empty config, we are not going to save this to disk
        pm = PluginManager(SafeConfigParser())

        # Add the plugin we are testing
        pm.add(self.plugin_dir)

        # The instance of our plugin we will run the pre_commit test on
        plugin = pm.plugins[0]

        # Capture the default plugin config for resets while testing
        default_settings = plugin.config

        results = []

        for exp in self.expectations:
            # Make sure that the range is off by 1
            assert exp.range[1] == exp.range[0] + 1

            # Is this expectation in the specified test range?
            if test_range and (exp.range not in test_range):
                # Skip this one, it's not one of the tests we should be running
                continue

            # Update the plugin config (settings) if available
            if exp.settings:
                plugin.config = exp.settings
            else:
                plugin.config = default_settings

            # View to help us create the output
            view = ConsoleView(collect_output=True, exit_on_exception=False)

            # Get a GitDiffIndex object from
            gdi = InstrumentedGitDiffIndex(self.timeline.repo.working_dir,
                self.timeline.diffs()[exp.range[0] - 1])

            # What is the numbered test directory reprsenting our commit?
            wd = abspath(join(self.plugin_dir, PLUGIN_TESTS_DIRECTORY,
                '{0:02d}'.format(exp.range[1])))

            with cwd_bounce(wd):
                # Patch up the filename to be within our numbered directory
                # instead of the Git repository
                gdi.replace_path = (self.timeline.repo.working_dir, wd)

                # Gather up the input to the plugin for logging
                stdin = json.dumps({'config': plugin.config,
                    'files': gdi}, indent=2, cls=PluginDataJSONEncoder)

                # Now run the actual pre_commit hook for this plugin
                res = plugin.pre_commit(gdi)
                # Break apart into its pieces
                retcode, stdout, stderr = res   # pragma: no branch

            try:
                # Is it JSON data?
                data = json.loads(stdout)
            except ValueError:
                # Not JSON
                data = stdout

            if retcode == 0:
                # Format the results according to what you normally see in the
                # console.
                view.print_results({plugin: (retcode, data, stderr)})
            else:
                results.append(FailureResult(exp,
                    'Exit code: {0}\n\nStd out:\n{1}\n\nStd err:\n{2}'.format(
                        retcode, stdout or '(none)', stderr or '(none)'),
                    plugin))
                continue

            # Now remove the color character sequences to make things a little
            # easier to read, copy, and paste.
            actual = strip_paint(view._collect['stdout'].getvalue() or
                view._collect['stderr'].getvalue())

            # Also remove the summary and count at the end, these are not
            # really all that useful to test and just end up making the
            # expect.rst files overly verbose
            actual = RESULTS_SUMMARY_SIGNATURE_RE.sub('', actual)
            actual = RESULTS_SUMMARY_COUNT_RE.sub('', actual)

            resargs = (exp, actual, plugin, stdin, stdout)
            if actual.strip() != exp.output.strip():
                results.append(FailureResult(*resargs))
            else:
                results.append(SuccessResult(*resargs))

        return results


class PluginTestReporter(object):

    """
    Formats a list of test results into human-readable format.

    The list must contain :py:class:`SuccessResult` or
    :py:class:`FailureResult' objects.

    """
    def __init__(self, results):
        self.results = results

    def _add_verbosity(self, out, stdin, stdout):
        """
        Formats the stdin and stdout into the output.
        """
        # Try to pretty print our data if it's JSON
        data = [stdin, stdout]
        for i in (0, 1):
            try:
                obj = json.loads(data[i])
                data[i] = json.dumps(obj, indent=2)
            except ValueError:
                # Wasn't JSON
                pass
            data[i] = indent(data[i].splitlines())

        out.append(u'stdin (sent to the plugin)')
        out.append(u'')
        out.extend(data[0])
        out.append(u'')
        out.append(u'stdout (received from the plugin)')
        out.append(u'')
        out.extend(data[1])
        out.append(u'')
        out.append(REPORTER_HORIZONTAL_DIVIDER)

    def dumps(self, verbose=False):
        """
        Formats a list of test results to unicode.

        The reporter can also output the value of what was sent to stdin and
        what the plugin sent to stdout if ``verbose`` is ``True``.
        """
        out = []

        results = self.results

        for result in results:
            exprange = result.expectation.range
            v_out = []

            if verbose:
                self._add_verbosity(v_out, result.stdin, result.stdout)

            if isinstance(result, SuccessResult):
                out.append(green_bold(u'{0:02d} – {1:02d} Pass'.format(
                    exprange[0], exprange[1])))
                out.append(u'')
                out.extend(v_out)
                continue

            out.append(red_bold(u'{0:02d} – {1:02d} Fail'.format(
                exprange[0], exprange[1])))

            out.extend(v_out)

            out.append(u'')

            out.append(u'Actual')
            out.append(REPORTER_HORIZONTAL_DIVIDER)
            out.append(u'')
            out.extend(result.actual.splitlines())
            out.append(u'')

            out.append(u'Diff')
            out.append(REPORTER_HORIZONTAL_DIVIDER)
            out.append(u'')

            diff = describe_diff(result.expectation.output, result.actual)
            for (_, diff_type, line) in diff:
                if diff_type == '-':
                    decorator = red_bold
                elif diff_type == '+':
                    decorator = green_bold
                else:
                    # No operation but return
                    decorator = lambda a: a

                out.append(decorator(u'{0} {1}'.format(diff_type, line)))

            out.append(u'')

        pass_count = len([i for i in results if isinstance(i, SuccessResult)])
        fail_count = len([i for i in results if isinstance(i, FailureResult)])

        out.append(u'Pass {0}, Fail {1}'.format(pass_count, fail_count))

        return u'\n'.join(out)


Expectation = namedtuple('Expectation', 'range settings output')


class plugin_settings_node(nodes.literal_block):

    """
    Represents a docutils node specific to plugin settings.

    """
    pass


class expectations_node(nodes.literal_block):

    """
    Represents the desired output from a plugin when tested.

    """
    pass


class PluginSettingsDirective(Directive):

    """
    Docutils directive for expressing plugin settings.

    Example::

        .. plugin-settings::

            underscore_in_filenames = no
            capital_letters_in_filenames = no
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        code = u'\n'.join(self.content)

        # Use the config parser to get our settings
        config_fp = StringIO('[settings]\n{0}'.format(code))
        config = SafeConfigParser()
        config.readfp(config_fp)
        node = plugin_settings_node(code, code)
        node.settings = dict(config.items('settings'))
        return [node]


class ExpectationDirective(Directive):

    """
    Docutils directive for documenting plugin settings.

    Example::

        .. expectation::
            :from: 01
            :to: 02

            ▾  File name checker

            ✓  New file looks OK (matches filename rules)
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 2
    final_argument_whitespace = True
    option_spec = {
        'from': directives.nonnegative_int,
        'to': directives.nonnegative_int}

    def run(self):
        code = u'\n'.join(self.content)
        node = expectations_node(code, code)

        # The from and to are required
        node.range = (self.options.get('from', None),
            self.options.get('to', None))

        if not node.range[0] or not node.range[1]:
            # The range is incomplete
            self.state_machine.reporter.error('expectation directive requires '
                '`to` and `from` arguments')

        return [node]


directives.register_directive('plugin-settings', PluginSettingsDirective)
directives.register_directive('expectation', ExpectationDirective)
