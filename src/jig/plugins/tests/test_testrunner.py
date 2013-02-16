# coding=utf-8
import json
from os import makedirs
from os.path import join, dirname
from codecs import open
from tempfile import mkdtemp
from textwrap import dedent
from copy import copy

from mock import patch

from jig.exc import (ExpectationNoTests, ExpectationFileNotFound,
    ExpectationParsingError)
from jig.tests.mocks import MockPlugin
from jig.conf import CODEC
from jig.tools import NumberedDirectoriesToGit
from jig.plugins import create_plugin, Plugin
from jig.tests.testcase import JigTestCase, PluginTestCase
from jig.output import ATTENTION, EXPLODE
from jig.plugins.testrunner import (PluginTestRunner,
    InstrumentedGitDiffIndex, PluginTestReporter, get_expectations,
    Expectation, Result, SuccessResult, FailureResult,
    REPORTER_HORIZONTAL_DIVIDER)

try:
    from collections import OrderedDict
except ImportError:   # pragma: no cover
    from ordereddict import OrderedDict


class TestResult(PluginTestCase):

    """
    Test the base class for success and failure results.

    """
    def test_requires_correct_args(self):
        """
        TypeError if missing arguments.
        """
        with self.assertRaises(TypeError):
            Result._make(tuple())

    def test_will_make_from_iterable(self):
        """
        Class method can create new results.
        """
        result = Result._make((None, None, None, None, None))

        self.assertEqual(
            'Result(expectation=None, actual=None, plugin=None, '
                'stdin=None, stdout=None)',
            repr(result))

    def test_convert_to_dict(self):
        """
        Can convert to a dictionary.
        """
        result = Result(None, None, None, None, None)

        self.assertEqual(OrderedDict([
            ('expectation', None),
            ('actual', None),
            ('plugin', None),
            ('stdin', None),
            ('stdout', None)]),
            result._asdict())

    def test_can_replace(self):
        """
        Can replace values.
        """
        result1 = Result(None, None, None, None, None)

        result2 = result1._replace(expectation=1, actual=1)

        self.assertEqual(
            'Result(expectation=1, actual=1, plugin=None, '
                'stdin=None, stdout=None)',
            repr(result2))

    def test_replace_checks_fields(self):
        """
        Replace will not work if the keyword is incorrect.
        """
        result = Result(None, None, None, None, None)

        with self.assertRaises(ValueError):
            result._replace(not_a_field=1)

    def test_can_copy(self):
        """
        Can copy.
        """
        result1 = Result(None, None, None, None, None)

        result2 = copy(result1)

        self.assertTrue(result1 == result2)
        self.assertFalse(result1 is result2)


class TestPluginTestRunner(PluginTestCase):

    """
    Test the ability for a plugin to test itself.

    """
    def setUp(self):
        super(TestPluginTestRunner, self).setUp()

        self.timeline_iter = 0

        self.plugindir = mkdtemp()

    def add_timeline(self, plugin_dir, files):
        """
        Adds a numbered directory with the contents from files.

        ``files`` should be a list of (filename, content). An example: ::

            self.add_timeline(plugin_dir, [
                ('a.txt', 'contents of a'),
                ('b.txt', 'contents of b')])
        """
        for filename, content in files:
            path = join(plugin_dir, 'tests',
                '{0:02d}'.format(self.timeline_iter + 1), filename)
            try:
                makedirs(dirname(path))
            except OSError:
                pass
            with open(path, 'w', CODEC) as fh:
                fh.write(content)   # pragma: no branch

        # Next run of the command will start a new numbered directory
        self.timeline_iter += 1

    def add_expectation(self, plugin_dir, content):
        """
        Creates the expect.rst file inside the plugin's test directory.
        """
        try:
            makedirs(join(plugin_dir, 'tests'))
        except OSError:
            pass

        with open(join(plugin_dir, 'tests', 'expect.rst'), 'w', CODEC) as fh:
            fh.write(dedent(content))

    def test_no_tests_to_run(self):
        """
        Plugin has no tests to run.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        # Since our newly created plugin has no tests, this should be empty
        with self.assertRaises(ExpectationNoTests) as ec:
            PluginTestRunner(plugin_dir)

        self.assertIn('Could not find any tests', str(ec.exception))

    def test_no_expectations(self):
        """
        We have a test timeline without any expectations.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])

        # Since our newly created plugin has no tests, this should be empty
        with self.assertRaises(ExpectationFileNotFound) as ec:
            PluginTestRunner(plugin_dir)

        self.assertIn('Missing expectation file', str(ec.exception))

    def test_loads_tests_and_expectations(self):
        """
        Will load the timeline and expecatations when created.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])
        self.add_expectation(plugin_dir, '''
            .. expectation::
                :from: 01
                :to: 02

                Test output''')

        ptr = PluginTestRunner(plugin_dir)

        # Just make sure that we have the expected objects
        self.assertIsInstance(ptr.timeline, NumberedDirectoriesToGit)
        self.assertIsInstance(ptr.expectations[0], Expectation)

    def test_success_result(self):
        """
        Will run the tests and detect a success result.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])
        self.add_expectation(plugin_dir, u'''
            .. expectation::
                :from: 01
                :to: 02

                ▾  plugin

                ✓  line 1: a.txt
                    a is -

                ✓  line 1: a.txt
                    aa is +''')

        ptr = PluginTestRunner(plugin_dir)

        results = ptr.run()

        self.assertEqual(1, len(results))
        self.assertIsInstance(results[0], SuccessResult)
        self.assertEqual(results[0].actual.strip(),
            results[0].expectation.output.strip())
        self.assertEqual((1, 2), results[0].expectation.range)

    def test_failure_result(self):
        """
        Will run the tests and detect a failure result.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])
        self.add_expectation(plugin_dir, u'''
            .. expectation::
                :from: 01
                :to: 02

                ▾  plugin

                ✓  Gobbildy gook''')

        ptr = PluginTestRunner(plugin_dir)

        results = ptr.run()

        self.assertEqual(1, len(results))
        self.assertIsInstance(results[0], FailureResult)

    def test_can_change_settings(self):
        """
        Altering the settings will be used correctly.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin',
            settings={'verbose': 'yes'})

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])

        self.add_expectation(plugin_dir, u'''
            .. plugin-settings::

                verbose = no

            .. expectation::
                :from: 01
                :to: 02

                ▾  plugin

                ✓  a.txt
                    File has been modified''')

        ptr = PluginTestRunner(plugin_dir)

        results = ptr.run()

        self.assertIsInstance(results[0], SuccessResult)

    def test_non_json_stdout(self):
        """
        Still processes if the plugin returns something other than JSON data.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])

        self.add_expectation(plugin_dir, u'''
            .. expectation::
                :from: 01
                :to: 02

                Output''')

        ptr = PluginTestRunner(plugin_dir)

        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (0, 'Non-JSON', '')

            results = ptr.run()

        self.assertResults(u'''
            ▾  plugin

            ✓  Non-JSON''', results[0].actual)

    def test_non_zero_exit_code(self):
        """
        If the exit code is non-zero, gets stderr instead.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin')

        self.add_timeline(plugin_dir, [('a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [('a.txt', 'aa\n')])

        self.add_expectation(plugin_dir, u'''
            .. expectation::
                :from: 01
                :to: 02

                Output''')

        ptr = PluginTestRunner(plugin_dir)

        with patch.object(Plugin, 'pre_commit'):
            Plugin.pre_commit.return_value = (1, '', 'Error')

            results = ptr.run()

        self.assertResults(u'''
            Exit code: 1

            Std out:
            (none)

            Std err:
            Error''', results[0].actual)

    def test_multiple_expectations(self):
        """
        Multiple tests can be ran.
        """
        plugin_dir = create_plugin(self.plugindir, 'bundle', 'plugin',
            settings={'verbose': 'no'})

        self.add_timeline(plugin_dir, [
            ('src/a.txt', 'a\n')])
        self.add_timeline(plugin_dir, [
            ('src/a.txt', 'aa\n')])
        self.add_timeline(plugin_dir, [
            ('src/a.txt', 'aaa\n')])
        self.add_timeline(plugin_dir, [
            ('src/a.txt', 'aaa\n'),
            ('src/b.txt', 'bbb\n')])

        self.add_expectation(plugin_dir, u'''
            .. expectation::
                :from: 01
                :to: 02

                ▾  plugin

                ✓  src/a.txt
                    File has been modified

            .. expectation::
                :from: 02
                :to: 03

                ▾  plugin

                ✓  src/a.txt
                    File has been modified

            .. expectation::
                :from: 03
                :to: 04

                ▾  plugin

                ✓  src/b.txt
                    File has been modified''')

        ptr = PluginTestRunner(plugin_dir)

        results = ptr.run()

        success = [isinstance(i, SuccessResult) for i in results]

        self.assertTrue(all(success))


class TestPluginTestReporter(PluginTestCase):

    """
    Results from a test run can be formatted for output.

    """
    def test_no_results(self):
        """
        No results reports nothing but the count.
        """
        results = []

        ptr = PluginTestReporter(results)

        self.assertEqual(u'Pass 0, Fail 0', ptr.dumps())

    def test_single_failure(self):
        """
        Reports a single failure.
        """
        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            FailureResult(actual=u'bbb', expectation=expectation,
                plugin=MockPlugin())]

        ptr = PluginTestReporter(results)

        self.assertResults(u'''
            01 – 02 Fail

            Actual
            {0}

            bbb

            Diff
            {0}

            - aaa
            + bbb

            Pass 0, Fail 1'''.format(REPORTER_HORIZONTAL_DIVIDER),
            ptr.dumps())

    def test_single_success(self):
        """
        Report a single success.
        """
        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin())]

        ptr = PluginTestReporter(results)

        self.assertResults(u'''
            01 – 02 Pass

            Pass 1, Fail 0''', ptr.dumps())

    def test_failure_within_success(self):
        """
        Multiple results.
        """
        expectation1 = Expectation((1, 2), None, u'aaa')
        expectation2 = Expectation((2, 3), None, u'b\nb\nb\n')
        expectation3 = Expectation((3, 4), None, u'ccc')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation1,
                plugin=MockPlugin()),
            FailureResult(actual=u'b\nB\nb\n', expectation=expectation2,
                plugin=MockPlugin()),
            SuccessResult(actual=u'ccc', expectation=expectation3,
                plugin=MockPlugin())]

        ptr = PluginTestReporter(results)

        self.assertResults(u'''
            01 – 02 Pass

            02 – 03 Fail

            Actual
            {0}

            b
            B
            b

            Diff
            {0}

              b
            + B
              b
            - b

            03 – 04 Pass

            Pass 2, Fail 1'''.format(REPORTER_HORIZONTAL_DIVIDER),
            ptr.dumps())

    def test_outputs_stdin_stdout(self):
        """
        Will report the input and output of a plugin.
        """
        stdin = json.dumps(['a', 'b', 'c'])
        stdout = json.dumps(['d', 'e', 'f'])

        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin(), stdin=stdin, stdout=stdout)]

        ptr = PluginTestReporter(results)

        self.assertResults(u'''
            01 – 02 Pass

            stdin (sent to the plugin)

                [
                  "a", 
                  "b", 
                  "c"
                ]

            stdout (received from the plugin)

                [
                  "d", 
                  "e", 
                  "f"
                ]

            {0}
            Pass 1, Fail 0'''.format(REPORTER_HORIZONTAL_DIVIDER),
            ptr.dumps(verbose=True))

    def tests_outputs_stdout_not_json(self):
        """
        Will report input and output, even if it's not JSON.
        """
        stdin = 'a\nb\nc\n'
        stdout = 'd\ne\nf\n'

        expectation = Expectation((1, 2), None, u'aaa')
        results = [
            SuccessResult(actual=u'aaa', expectation=expectation,
                plugin=MockPlugin(), stdin=stdin, stdout=stdout)]

        ptr = PluginTestReporter(results)

        self.assertResults(u'''
            01 – 02 Pass

            stdin (sent to the plugin)

                a
                b
                c

            stdout (received from the plugin)

                d
                e
                f

            {0}
            Pass 1, Fail 0'''.format(REPORTER_HORIZONTAL_DIVIDER),
            ptr.dumps(verbose=True))


class TestGetExpectations(PluginTestCase):

    """
    Test converting reStructuredText documents into :py:class:`Expectation`.

    """
    def test_missing_arguments(self):
        """
        Expectation directives have two options.
        """
        with self.assertRaises(ExpectationParsingError) as ec:
            list(get_expectations(dedent('''
                .. expectation::

                    Line 1
                ''')))

        self.assertIn(
            'expectation directive requires `to` and `from` arguments',
            str(ec.exception))

    def test_non_integer_arguments(self):
        """
        Expectation directives have two required arguments.
        """
        with self.assertRaises(ExpectationParsingError) as ec:
            list(get_expectations(dedent('''
                .. expectation::
                    :to: a
                    :from: b

                    Line 1
                ''')))

        self.assertIn('Error in "expectation" directive',
            str(ec.exception))
        # And it's warning us about not being able to convert to an integer
        self.assertIn('invalid literal for int()',
            str(ec.exception))

    def test_expectation_no_settings(self):
        """
        Expectation with no accompanying settings.
        """
        exps = list(get_expectations(dedent('''
            Title 1
            =======

            .. expectation::
                :from: 01
                :to: 02

                Output''')))

        self.assertEqual(1, len(exps))
        self.assertEqual(
            Expectation(range=(1, 2), settings=None, output=u'Output'),
            exps[0])

    def test_settings(self):
        """
        Expectation with settings.
        """
        exps = list(get_expectations(dedent('''
            Title 1
            =======

            .. plugin-settings::

                a = 1
                b = 2

            .. expectation::
                :from: 01
                :to: 02

                Output''')))

        self.assertEqual(1, len(exps))
        self.assertEqual(
            Expectation((1, 2), {'a': '1', 'b': '2'}, u'Output'),
            exps[0])

    def test_settings_at_distance(self):
        """
        If settings are separated by other non structural nodes.
        """
        exps = list(get_expectations(dedent('''
            Title 1
            =======

            .. plugin-settings::

                a = 1
                b = 2

            Paragraph 1

            Paragraph 2

            .. expectation::
                :from: 01
                :to: 02

                Output''')))

        self.assertEqual(
            Expectation((1, 2), {'a': '1', 'b': '2'}, u'Output'),
            exps[0])

    def test_multiple_expectations(self):
        """
        More than one expectation.
        """
        exps = list(get_expectations(dedent('''
            Title 1
            =======

            .. plugin-settings::

                a = 1

            .. expectation::
                :from: 01
                :to: 02

                Output 1

            Title 2
            =======

            .. plugin-settings::

                a = 1

            .. expectation::
                :from: 02
                :to: 03

                Output 2''')))

        self.assertEqual([
            Expectation((1, 2), {'a': '1'}, u'Output 1'),
            Expectation((2, 3), {'a': '1'}, u'Output 2')],
            exps)


class TestInstrumentedGitDiffIndex(JigTestCase):

    """
    The instrumented GitDiffIndex provides extra features for testing.

    """
    def setUp(self):
        super(TestInstrumentedGitDiffIndex, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.testrepo = repo
        self.testrepodir = working_dir
        self.testdiffs = diffs

    def test_no_replacement(self):
        """
        Will not make any replacements if not configured to.
        """
        igdi = InstrumentedGitDiffIndex(self.testrepo, self.testdiffs[0])

        filenames = [i['filename'] for i in igdi.files()]

        self.assertEqual(1, len(filenames))
        self.assertEqual(
            '{0}/argument.txt'.format(self.testrepodir),
            filenames[0])

    def test_will_replace(self):
        """
        Will replace part of the filename path with something else.
        """
        igdi = InstrumentedGitDiffIndex(self.testrepo, self.testdiffs[0])

        igdi.replace_path = (self.testrepodir, '/path')

        filenames = [i['filename'] for i in igdi.files()]

        self.assertEqual(1, len(filenames))
        self.assertEqual(
            '/path/argument.txt', filenames[0])
