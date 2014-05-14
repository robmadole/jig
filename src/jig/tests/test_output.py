# coding=utf-8
from StringIO import StringIO

from jig.tests import factory
from jig.tests.testcase import JigTestCase
from jig.tests.mocks import MockPlugin
from jig.formatters.utils import green_bold, yellow_bold, red_bold
from jig.output import (
    strip_paint, utf8_writer, Message, Error, ResultsCollator)


class TestStripPaint(JigTestCase):

    """
    Can remove the terminal escape sequences.

    """
    def test_strips_green(self):
        """
        Strips the green color.
        """
        self.assertEqual(
            'Green',
            strip_paint(green_bold('Green'))
        )

    def test_strips_yellow(self):
        """
        Strips the yellow color.
        """
        self.assertEqual(
            'Yellow',
            strip_paint(yellow_bold('Yellow'))
        )

    def test_strips_red(self):
        """
        Strips the red color.
        """
        self.assertEqual(
            'Red',
            strip_paint(red_bold('Red'))
        )


class TestUTF8Writer(JigTestCase):

    """
    File-like objects can be wrapped to output utf-8.

    """
    def test_writes_utf8(self):
        """
        Writes utf-8 encoded strings to the file object.
        """
        collector = StringIO()

        writer = utf8_writer(collector)

        writer.write(u'☆')

        self.assertEqual(collector.getvalue(), '\xe2\x98\x86')


class TestMessage(JigTestCase):

    """
    Test Message which is responsible for representing output from plugins.

    """
    def test_representation(self):
        """
        Object's representation is correct.
        """
        message = Message(None, type='w', file='a.txt', body='body', line=1)

        self.assertEqual(
            "<Message type=\"warn\", body='body', file='a.txt', line=1>",
            repr(message))

        message = Message(None, type='stop', file='a.txt', body=True, line=1)

        self.assertEqual(
            "<Message type=\"stop\", body=True, file='a.txt', line=1>",
            repr(message))

    def test_equality(self):
        """
        Messages with the same content are considered equal.
        """
        message1 = Message(
            MockPlugin(), type='w', file='a.txt', body='body', line=1
        )
        message2 = Message(
            MockPlugin(), type='w', file='a.txt', body='body', line=1
        )
        message3 = Message(
            MockPlugin(), type='w', file='b.txt', body='bbbb', line=9
        )

        self.assertTrue(message1 == message2)
        self.assertFalse(message2 == message3)
        self.assertFalse(message3 == {})


class TestResultsCollator(JigTestCase):

    """
    Collate results into digestible summaries.

    """
    def test_plugin_error(self):
        """
        Results with non-zero exit codes create error messages.
        """
        rc = ResultsCollator(factory.error())

        cm, fm, lm = rc.messages

        self.assertEqual(
            [Error(None, type='stop', body='Plugin failed')],
            rc.errors)

    def test_empty_dict(self):
        """
        Empty dict do not generate empty messages.
        """
        rc = ResultsCollator({})

        self.assertEqual(0, len(rc.plugins))
        self.assertEqual(0, len(rc.reporters))

    def test_no_results(self):
        """
        We have results but no real content.
        """
        rc = ResultsCollator(factory.no_results())

        cm, fm, lm = rc.messages

        # Should all be empty since nothing of interest was found
        self.assertEqual([], cm)
        self.assertEqual([], fm)
        self.assertEqual([], lm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_commit_specific_message(self):
        """
        Results that are commit specific are collated correctly.
        """
        rc = ResultsCollator(factory.commit_specific_message())

        messages, fm, lm = rc.messages

        # Defaults to info type
        self.assertEqual(
            Message(None, type='info', body='default'),
            messages[0]
        )
        self.assertEqual(
            Message(None, type='warn', body='warning'),
            messages[1]
        )

        # And our type counts should be 1 info 1 warning
        self.assertEqual({u'info': 1, u'warn': 1, u'stop': 0}, rc.counts)

        # The rest of these should be empty
        self.assertEqual([], fm)
        self.assertEqual([], lm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_file_specific_message(self):
        """
        Results that are file-specific are collated correctly.
        """
        rc = ResultsCollator(factory.file_specific_message())

        self.assertEqual({u'info': 1, u'warn': 3, u'stop': 1}, rc.counts)

        cm, messages, lm = rc.messages

        for msg in messages:
            # They all lack a line number, making them file-specific.
            self.assertIsNone(msg.line)
            # But they have a file
            self.assertIsNotNone(msg.file)

        # First set's None get's recognized as file-specific
        self.assertEqual(
            Message(
                None, type='warn',
                body='Problem with this file', file='a.txt'
            ),
            messages[0])

        # Second set get's recognized as a warning
        self.assertEqual(
            Message(
                None, type='warn',
                body='Problem with this file', file='a.txt'
            ),
            messages[1])

        self.assertEqual(
            Message(
                None, type='info',
                body='Info A', file='a.txt'
            ),
            messages[2])
        self.assertEqual(
            Message(
                None, type='warn',
                body='Warn B', file='b.txt'
            ),
            messages[3])
        self.assertEqual(
            Message(
                None, type='stop',
                body='Stop C', file='c.txt'
            ),
            messages[4])

        # The other messages should be empty
        self.assertEqual([], cm)
        self.assertEqual([], lm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_line_specific_message(self):
        """
        Results that are line-specific are collated correctly.
        """
        rc = ResultsCollator(factory.line_specific_message())

        self.assertEqual({u'info': 1, u'warn': 1, u'stop': 1}, rc.counts)

        cm, fm, messages = rc.messages

        self.assertEqual(
            Message(None, type='info', body='Info A', file=u'a.txt', line=1),
            messages[0])
        self.assertEqual(
            Message(None, type='warn', body='Warn B', file=u'b.txt', line=2),
            messages[1])
        self.assertEqual(
            Message(None, type='stop', body='Stop C', file=u'c.txt', line=3),
            messages[2])

        # The other messages should be empty
        self.assertEqual([], cm)
        self.assertEqual([], fm)

        # And we should have no errors
        self.assertEqual([], rc.errors)

    def test_one_of_each(self):
        """
        One of each type of message is captured.
        """
        rc = ResultsCollator(factory.one_of_each())

        self.assertEqual({u'info': 3, u'warn': 0, u'stop': 0}, rc.counts)

        cm, fm, lm = rc.messages

        self.assertEqual(1, len(cm))
        self.assertEqual(1, len(fm))
        self.assertEqual(1, len(lm))

        self.assertEqual(
            Message(None, type="info", body="C"),
            cm[0])
        self.assertEqual(
            Message(None, type="info", body="F", file=u'a.txt'),
            fm[0])
        self.assertEqual(
            Message(None, type="info", body="L", file=u'a.txt', line=1),
            lm[0])

    def test_commit_specific_errors(self):
        """
        Exercise the errors related to commit specific messages.
        """
        rc = ResultsCollator(factory.commit_specific_error())

        self.assertEqual(
            Error(None, type='s', body=factory.anon_obj),
            rc.errors[0])

        self.assertEqual(
            Error(None, type='s', body=[1, 2, 3, 4, 5]),
            rc.errors[1])

    def test_file_specific_errors(self):
        """
        Exercise the errors related to file specific messages.
        """
        rc = ResultsCollator(factory.file_specific_error())

        self.assertEqual(
            Error(None, type='s', file='a.txt', body=factory.anon_obj),
            rc.errors[0])

        self.assertEqual(
            Error(None, type='s', file='a.txt', body=factory.anon_obj),
            rc.errors[1])

        self.assertEqual([
            Error(None, type='s', file='a.txt', body=1),
            Error(None, type='s', file='a.txt', body=None)],
            rc.errors[2:4])

        self.assertEqual(
            Error(None, type='s', body={'a.txt': [[1, 2, 3, 4, 5]]}),
            rc.errors[4])
