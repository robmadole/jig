# coding=utf-8
from jig.tests import factory
from jig.tests.testcase import JigTestCase, FormatterTestCase
from jig.output import Message
from jig.formatters.tap import TapFormatter, _format_description


class TestTapFormatDescription(JigTestCase):

    """
    Messages can be formatted into descriptions.

    """
    def test_empty_message(self):
        """
        Message with no line number but file-specific.
        """
        self.assertEqual(
            '',
            _format_description(Message(plugin=None))
        )

    def test_body_message(self):
        """
        Message with no line number but file-specific.
        """
        self.assertEqual(
            ' - body',
            _format_description(Message(plugin=None, body='body'))
        )

    def test_file_message(self):
        """
        Message with no line number but file-specific.
        """
        self.assertEqual(
            ' - a.txt',
            _format_description(Message(plugin=None, file='a.txt'))
        )

    def test_file_with_line_message(self):
        self.assertEqual(
            ' - a.txt:1',
            _format_description(Message(plugin=None, file='a.txt', line=1))
        )


class TestTapFormatter(FormatterTestCase):

    """
    Tests results can be formatted for TAP (Test Anything Protocol)

    """
    formatter = TapFormatter

    def test_empty_dict(self):
        """
        Empty results dict.
        """
        printed = self.run_formatter({})

        self.assertResults(
            u"""
            TAP version 13
            1..0
            """,
            printed
        )

    def test_no_results(self):
        """
        No results.
        """
        printed = self.run_formatter(factory.no_results())

        self.assertResults(
            u"""
            TAP version 13
            1..0
            """,
            printed
        )

    def test_commit_specific_message(self):
        """
        Commit-specific message.
        """
        printed = self.run_formatter(factory.commit_specific_message())

        self.assertResults(
            u"""
            TAP version 13
            1..2
            ok 1 - default
              ---
              plugin: Unnamed
              severity: info
              ...
            not ok 2 - warning
              ---
              plugin: Unnamed
              severity: warn
              ...
            """,
            printed
        )

    def test_file_specific_message(self):
        """
        File-specific message.
        """
        printed = self.run_formatter(factory.file_specific_message())

        self.assertResults(
            u"""
            TAP version 13
            1..5
            not ok 1 - a.txt
              ---
              message: Problem with this file
              plugin: Unnamed
              severity: warn
              ...
            not ok 2 - a.txt
              ---
              message: Problem with this file
              plugin: Unnamed
              severity: warn
              ...
            ok 3 - a.txt
              ---
              message: Info A
              plugin: Unnamed
              severity: info
              ...
            not ok 4 - b.txt
              ---
              message: Warn B
              plugin: Unnamed
              severity: warn
              ...
            not ok 5 - c.txt
              ---
              message: Stop C
              plugin: Unnamed
              severity: stop
              ...
            """,
            printed
        )

    def test_line_specific_message(self):
        """
        Line-specific message.
        """
        printed = self.run_formatter(factory.line_specific_message())

        self.assertResults(
            u"""
            TAP version 13
            1..3
            ok 1 - a.txt:1
              ---
              message: Info A
              plugin: Unnamed
              severity: info
              ...
            not ok 2 - b.txt:2
              ---
              message: Warn B
              plugin: Unnamed
              severity: warn
              ...
            not ok 3 - c.txt:3
              ---
              message: Stop C
              plugin: Unnamed
              severity: stop
              ...
            """,
            printed
        )

    def test_one_of_each(self):
        """
        One of each message.
        """
        printed = self.run_formatter(factory.one_of_each())

        self.assertResults(
            u"""
            TAP version 13
            1..3
            ok 1 - C
              ---
              plugin: Unnamed
              severity: info
              ...
            ok 2 - a.txt
              ---
              message: F
              plugin: Unnamed
              severity: info
              ...
            ok 3 - a.txt:1
              ---
              message: L
              plugin: Unnamed
              severity: info
              ...
            """,
            printed
        )

    def test_commit_specific_error(self):
        """
        Commit-specific error.
        """
        printed = self.run_formatter(factory.commit_specific_error())

        self.assertResults(
            u"""
            TAP version 13
            1..2
            not ok 1 - {0}
              ---
              plugin: Unnamed
              severity: stop
              ...
            not ok 2 - [[1, 2, 3, 4, 5]]
              ---
              plugin: Unnamed
              severity: stop
              ...
            """.format(factory.anon_obj),
            printed
        )

    def test_file_specific_error(self):
        """
        File-specific error.
        """
        printed = self.run_formatter(factory.file_specific_error())

        self.assertResults(
            u"""
            TAP version 13
            1..4
            not ok 1 - {{'a.txt': {0}}}
              ---
              plugin: Unnamed
              severity: stop
              ...
            not ok 2 - {{'a.txt': [{0}]}}
              ---
              plugin: Unnamed
              severity: stop
              ...
            not ok 3 - {{'a.txt': [1, None]}}
              ---
              plugin: Unnamed
              severity: stop
              ...
            not ok 4 - {{'a.txt': [[1, 2, 3, 4, 5]]}}
              ---
              plugin: Unnamed
              severity: stop
              ...
            """.format(factory.anon_obj),
            printed
        )
