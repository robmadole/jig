# coding=utf-8
import json
from codecs import open
from os.path import join
from StringIO import StringIO
from collections import namedtuple
from ConfigParser import SafeConfigParser

from docutils import nodes, core, io
from docutils.parsers.rst import Directive, directives

from becareful.exc import (ExpectationNoTests, ExpectationFileNotFound,
    ExpectationParsingError)
from becareful.conf import CODEC, PLUGIN_EXPECTATIONS_FILENAME
from becareful.tools import NumberedDirectoriesToGit
from becareful.output import ConsoleView, strip_paint
from becareful.plugins import PluginManager
from becareful.diffconvert import GitDiffIndex


# What docutil nodes signify a structural or sectional break
DOCUTILS_DIFFERENT_SECTION_NODES = (nodes.Root, nodes.Structural,
    nodes.Titular)


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


Result = namedtuple('Result', 'expectation actual plugin')


class SuccessResult(Result):

    """
    The expectation for a single plugins tests matched its output.

    """
    def __repr__(self):   # pragma: no cover
        return '<SuccessResult from={} to={}>'.format(*self.expectation.range)


class FailureResult(Result):

    """
    The expectation for a single plugins tests does not match its output.

    """
    def __repr__(self):   # pragma: no cover
        return '<FailureResult from={} to={}>'.format(*self.expectation.range)


class PluginTestRunner(object):

    """
    Run tests to verify a plugin functions as expected.

    """
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.timeline = None
        self.expectations = None

        try:
            test_directory = join(plugin_dir, 'tests')
            self.timeline = NumberedDirectoriesToGit(test_directory)
        except ValueError:
            raise ExpectationNoTests('Could not find any tests: {}'.format(
                test_directory))

        try:
            expect_filename = join(plugin_dir, 'tests',
                PLUGIN_EXPECTATIONS_FILENAME)

            with open(expect_filename, 'r', CODEC) as fh:
                expectation_text = fh.read()

            self.expectations = list(get_expectations(expectation_text))
        except (IOError, OSError):
            raise ExpectationFileNotFound(
                'Missing expectation file: {}'.format(expect_filename))

    def run(self):
        """
        Run the tests for this plugin.

        Returns a list of :py:class:`Result` objects which represent the
        results from the test run.
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

            # Update the plugin config (settings) if available
            if exp.settings:
                plugin.config = exp.settings
            else:
                plugin.config = default_settings

            # View to help us create the output
            view = ConsoleView(collect_output=True, exit_on_exception=False)

            # Get a GitDiffIndex object from
            gdi = GitDiffIndex(self.timeline.repo.working_dir,
                self.timeline.diffs()[exp.range[0] - 1])

            # Now run the actual pre_commit hook for this plugin
            retcode, stdout, stderr = plugin.pre_commit(gdi)

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
                results.append(FailureResult(exp, stderr, plugin))
                continue

            # Now remove the color character sequences to make things a little
            # easier to read, copy, and paste.
            actual = strip_paint(view._collect['stdout'].getvalue() or
                view._collect['stderr'].getvalue())

            resargs = (exp, actual, plugin)
            if actual.strip() != exp.output.strip():
                results.append(FailureResult(*resargs))
            else:
                results.append(SuccessResult(*resargs))

        return results


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

            underscore_in_filenames = false
            capital_letters_in_filenames = false
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        code = u'\n'.join(self.content)

        # Use the config parser to get our settings
        config_fp = StringIO('[settings]\n{}'.format(code))
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

            Ran 1 plugin
                Info 1 Warn 0 Stop 0
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
