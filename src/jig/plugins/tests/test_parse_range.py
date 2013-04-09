from unittest import TestCase

from jig.exc import RangeError
from jig.plugins.testrunner import parse_range


class TestParseRange(TestCase):

    """
    Parses a string range into a list.

    Valid ranges look like ``2..4`` or ``6..7``.

    """
    def test_missing_dots(self):
        """
        Raises an error if the two dots are missing.
        """
        with self.assertRaises(RangeError):
            parse_range('1.3')

    def test_invalid_numbers(self):
        """
        Checks for numbers.
        """
        with self.assertRaises(RangeError):
            parse_range('a..3')

    def test_second_number_is_greater(self):
        """
        The second number is greater than the first.
        """
        with self.assertRaises(RangeError):
            parse_range('2..1')

        with self.assertRaises(RangeError):
            parse_range('2..2')

    def test_simple_range(self):
        """
        Should result in just one test set.
        """
        self.assertEqual(
            parse_range('1..2'),
            [(1, 2)])

    def test_complex_range(self):
        """
        Should result in more than one.
        """
        self.assertEqual(
            parse_range('4..8'),
            [(4, 5), (5, 6), (6, 7), (7, 8)])

    def test_large_numbers(self):
        """
        Large numbers with zero padding on the left.
        """
        self.assertEqual(
            len(parse_range('040..050')),
            10)
