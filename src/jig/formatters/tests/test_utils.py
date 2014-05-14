from jig.tests.testcase import JigTestCase

from jig.formatters.utils import green_bold, yellow_bold, red_bold


class TestColors(JigTestCase):

    """
    Colors can be formatted for the terminal.

    """
    def test_green_bold(self):
        """
        Green bold.
        """
        self.assertEqual(
            u'\x1b[32;1mGreen\x1b[39;22m',
            green_bold('Green')
        )

    def test_yellow_bold(self):
        """
        Yellow bold.
        """
        self.assertEqual(
            u'\x1b[33;1mYellow\x1b[39;22m',
            yellow_bold('Yellow')
        )

    def test_red_bold(self):
        """
        Red bold.
        """
        self.assertEqual(
            u'\x1b[31;1mRed\x1b[39;22m',
            red_bold('Red')
        )
