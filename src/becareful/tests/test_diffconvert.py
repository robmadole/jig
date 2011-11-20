from os.path import dirname, join, realpath
from unittest import TestCase
from functools import wraps
from textwrap import dedent
from pprint import PrettyPrinter
from operator import itemgetter

from nose.plugins.attrib import attr

from becareful.tests.testcase import BeCarefulTestCase
from becareful.tools import NumberedDirectoriesToGit
from becareful.diffconvert import GitDiffIndex, describe_diff


def assertDiff(func):
    """
    Decorator used to test diffs.

    Uses ``yield`` in the following way:

        @assertDiff
        def test_my_diff(self):
            yield 'one'

            yield 'two'

            yield [(1, '-', 'one'), (1, '+', 'two')]

    The order of the yields are:

        1. Original value (a)
        2. After it's edited (b)
        3. The expected difference
    """
    pp = PrettyPrinter().pformat

    @wraps(func)
    def wrapper(self, **kwargs):
        queue = func(self, **kwargs)

        a = queue.next()
        b = queue.next()
        expected = queue.next()

        a = dedent(a).strip()
        b = dedent(b).strip()

        actual = [i for i in describe_diff(a, b)]
        if not expected == actual:
            self.fail('Diff does not match:\nexpected\n{}\nactual\n{}'.format(
                pp(expected),
                pp(actual)))

    return wrapper


class TestDescribeDiff(TestCase):
    """
    Test our diff description method.
    """
    @assertDiff
    def test_all_addition(self):
        yield ''

        yield '''
            one
            two
            three'''

        yield [
            (1, '+', 'one'),
            (2, '+', 'two'),
            (3, '+', 'three')]

    @assertDiff
    def test_add_blank_lines(self):
        yield '''
            one
            two
            three'''

        yield '''
            one


            two
            three'''

        # This is a bit counter-intuitive, but correct
        yield [
            (1, ' ', 'one'),
            (2, '+', ''),
            (3, '+', ''),
            (4, ' ', 'two'),
            (5, ' ', 'three')]

    @assertDiff
    def test_all_same(self):
        yield '''
            one
            two
            three'''

        yield '''
            one
            two
            three'''

        yield [
            (1, ' ', 'one'),
            (2, ' ', 'two'),
            (3, ' ', 'three')]

    @assertDiff
    def test_one_insert(self):
        yield '''
            one
            two
            three'''

        yield '''
            one
            two
            2.5
            three'''

        yield [
            (1, ' ', 'one'),
            (2, ' ', 'two'),
            (3, '+', '2.5'),
            (4, ' ', 'three')]

    @assertDiff
    def test_one_delete(self):
        yield '''
            one
            two
            three
            four'''

        yield '''
            one
            two
            four'''

        yield [
            (1, ' ', 'one'),
            (2, ' ', 'two'),
            (3, '-', 'three'),
            (3, ' ', 'four')]

    @assertDiff
    def test_one_insert_delete(self):
        yield '''
            one
            two
            three
            four'''

        yield '''
            one
            two
            3
            four'''

        yield [
            (1, ' ', 'one'),
            (2, ' ', 'two'),
            (3, '-', 'three'),
            (3, '+', '3'),
            (4, ' ', 'four')]

    @assertDiff
    def test_one_character_change(self):
        yield '''
            one
            two
            three
            four'''

        yield '''
            one
            two
            thr3e
            four'''

        yield [
            (1, ' ', 'one'),
            (2, ' ', 'two'),
            (3, '-', 'three'),
            (3, '+', 'thr3e'),
            (4, ' ', 'four')]

    @assertDiff
    def test_complex_01(self):
        yield '''
            one
            two
            three
            three-and-a-smidge
            four'''

        yield '''
            one
            1.5
            two
            three

            four'''

        yield [
            (1, ' ', 'one'),
            (2, '+', '1.5'),
            (3, ' ', 'two'),
            (4, ' ', 'three'),
            (4, '-', 'three-and-a-smidge'),
            (5, '+', ''),
            (6, ' ', 'four')]


class TestGitDiffIndex(BeCarefulTestCase):

    """
    Test converting git changes to JSON.

    """
    def setUp(self):
        super(TestGitDiffIndex, self).setUp()

        repo, working_dir, diffs = self.repo_from_fixture('repo01')

        self.testrepo = repo
        self.testrepodir = working_dir
        self.testdiffs = diffs

    def test_new_file(self):
        """
        Handles new files.
        """
        gdi = self.git_diff_index(self.testrepo, self.testdiffs[0])

        self.assertEqual(1, len(list(gdi.files())))

        file1 = gdi.files().next()

        # This one is relative to the git repo
        self.assertEqual('argument.txt', file1['name'])
        # It should be added because this is a new file
        self.assertEqual('added', file1['type'])
        # This one is the full path to the file
        self.assertEqual(realpath(join(self.testrepodir, 'argument.txt')),
            realpath(file1['filename']))

    def test_modified(self):
        """
        Handles modified files.
        """
        gdi = self.git_diff_index(self.testrepo, self.testdiffs[1])

        self.assertEqual(1, len(list(gdi.files())))

        file1 = gdi.files().next()
        diff = [i for i in file1['diff']]
        difftypes = set([i[1] for i in diff])

        # File was changed
        self.assertEqual('modified', file1['type'])

        # We should have every kind of modification
        # Same lines, additions, and subtractions
        self.assertEqual(
            set([' ', '+', '-']),
            difftypes)

        # And we have a list of differences as expected
        self.assertEqual(47, len(diff))

    def test_deleted_file(self):
        """
        Handles deleted files.
        """
        gdi = self.git_diff_index(self.testrepo, self.testdiffs[2])

        self.assertEqual(1, len(list(gdi.files())))

        file1 = gdi.files().next()
        diff = [i for i in file1['diff']]
        difftypes = set([i[1] for i in diff])

        # File was deleted
        self.assertEqual('deleted', file1['type'])

        # Each line should be a removal
        self.assertEqual(
            set(['-']),
            difftypes)

        self.assertEqual(35, len(diff))

    def test_multiple_changes(self):
        """
        Handles multiple files changed.
        """
        gdi = self.git_diff_index(self.testrepo, self.testdiffs[3])

        self.assertEqual(2, len(list(gdi.files())))

        files = sorted([i for i in gdi.files()],
            key=itemgetter('name'))

        self.assertEqual('famous-deaths.txt',
            files[0]['name'])

        self.assertEqual('italian-lesson.txt',
            files[1]['name'])
