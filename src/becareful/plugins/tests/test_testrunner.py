# coding=utf-8
from os import makedirs
from codecs import open
from os.path import join, dirname
from tempfile import mkdtemp
from textwrap import dedent

from becareful.exc import (ExpectationNoTests, ExpectationFileNotFound,
    ExpectationParsingError)
from becareful.conf import CODEC
from becareful.tools import NumberedDirectoriesToGit
from becareful.plugins import create_plugin
from becareful.tests.testcase import PluginTestCase
from becareful.plugins.testrunner import (PluginTestRunner, get_expectations,
    Expectation, SuccessResult, FailureResult)


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
                fh.write(content)
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

        self.assertIn('Could not find any tests', ec.exception.message)

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

        self.assertIn('Missing expectation file', ec.exception.message)

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
                    aa is +

                Ran 1 plugin
                    Info 2 Warn 0 Stop 0''')

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

                ✓  Gobbildy gook

                Ran 1 plugin
                    Info 2 Warn 0 Stop 0''')

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
                    File has been modified

                Ran 1 plugin
                    Info 1 Warn 0 Stop 0''')

        ptr = PluginTestRunner(plugin_dir)

        results = ptr.run()

        self.assertIsInstance(results[0], SuccessResult)

    def test_non_json_stdout(self):
        pass

    def test_non_zero_exit_code(self):
        pass

    def test_multiple_expectations(self):
        pass


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
            ec.exception.message)

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
            ec.exception.message)
        # And it's warning us about not being able to convert to an integer
        self.assertIn('invalid literal for int()',
            ec.exception.message)

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
