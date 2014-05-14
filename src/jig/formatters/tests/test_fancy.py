# coding=utf-8
from jig.tests import factory
from jig.tests.testcase import FormatterTestCase
from jig.formatters.fancy import FancyFormatter, OK_SIGN, ATTENTION, EXPLODE


class TestFancyFormatter(FormatterTestCase):

    """
    Tests results can be formatted in the fancy way.

    """
    formatter = FancyFormatter

    def test_empty_dict(self):
        """
        Empty results dict.
        """
        printed = self.run_formatter({})

        self.assertResults(
            u"""
            {0}  Jig ran 0 plugins, nothing to report
            """.format(OK_SIGN),
            printed
        )

    def test_no_results(self):
        """
        No results.
        """
        printed = self.run_formatter(factory.no_results())

        self.assertResults(
            u"""
            {0}  Jig ran 10 plugins, nothing to report
            """.format(OK_SIGN),
            printed
        )

    def test_commit_specific_message(self):
        """
        Commit-specific message.
        """
        printed = self.run_formatter(factory.commit_specific_message())

        self.assertResults(
            u"""
            ▾  Unnamed

            ✓  default

            ▾  Unnamed

            ⚠  warning

            {0}  Jig ran 2 plugins
                Info 1 Warn 1 Stop 0""".format(ATTENTION),
            printed
        )

    def test_file_specific_message(self):
        """
        File-specific message.
        """
        printed = self.run_formatter(factory.file_specific_message())

        self.assertResults(
            u"""
            ▾  Unnamed

            ⚠  a.txt
                Problem with this file

            ▾  Unnamed

            ⚠  a.txt
                Problem with this file

            ▾  Unnamed

            ✓  a.txt
                Info A

            ⚠  b.txt
                Warn B

            ✕  c.txt
                Stop C

            {0}  Jig ran 3 plugins
                Info 1 Warn 3 Stop 1""".format(EXPLODE),
            printed
        )

    def test_line_specific_message(self):
        """
        Line-specific message.
        """
        printed = self.run_formatter(factory.line_specific_message())

        self.assertResults(
            u"""
            ▾  Unnamed

            ✓  line 1: a.txt
                Info A

            ⚠  line 2: b.txt
                Warn B

            ✕  line 3: c.txt
                Stop C

            {0}  Jig ran 1 plugin
                Info 1 Warn 1 Stop 1""".format(EXPLODE),
            printed
        )

    def test_one_of_each(self):
        """
        One of each message.
        """
        printed = self.run_formatter(factory.one_of_each())

        self.assertResults(
            u"""
            ▾  Unnamed

            ✓  C

            ▾  Unnamed

            ✓  a.txt
                F

            ▾  Unnamed

            ✓  line 1: a.txt
                L

            {0}  Jig ran 3 plugins
                Info 3 Warn 0 Stop 0""".format(ATTENTION),
            printed
        )

    def test_commit_specific_error(self):
        """
        Commit-specific error.
        """
        printed = self.run_formatter(factory.commit_specific_error())

        self.assertResults(
            u"""
            ▾  Unnamed

            ✕  {0}

            ▾  Unnamed

            ✕  [1, 2, 3, 4, 5]

            {1}  Jig ran 2 plugins
                Info 0 Warn 0 Stop 0
                (2 plugins reported errors)
            """.format(factory.anon_obj, ATTENTION),
            printed
        )

    def test_file_specific_error(self):
        """
        File-specific error.
        """
        printed = self.run_formatter(factory.file_specific_error())

        self.assertResults(
            u"""
            ▾  Unnamed

            ✕  a.txt
                {0}

            ▾  Unnamed

            ✕  a.txt
                {0}

            ▾  Unnamed

            ✕  a.txt
                1

            ✕  a.txt
                None

            ▾  Unnamed

            ✕  {{'a.txt': [[1, 2, 3, 4, 5]]}}

            {1}  Jig ran 4 plugins
                Info 0 Warn 0 Stop 0
                (5 plugins reported errors)
            """.format(factory.anon_obj, ATTENTION),
            printed
        )
