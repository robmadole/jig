# coding=utf-8
from os.path import join, dirname

from jig.gitutils.commands import git
from jig.tools import NumberedDirectoriesToGit, slugify, indent
from jig.tests.testcase import JigTestCase


def diff_tree(repo, rev):
    return git(repo)(
        'diff-tree',
        '-r',
        '--root',
        '--name-only',
        '--no-commit-id',
        '-r',
        rev
    ).splitlines()


class TestSlugify(JigTestCase):

    """
    Converting strings into slugs.

    """
    def test_nothing(self):
        """
        An empty string is given.
        """
        self.assertEqual(u'', slugify(u''))

    def test_normal_ascii_string(self):
        """
        ASCII string.
        """
        self.assertEqual(u'abc-def-ghi', slugify(u'Abc & Def Ghi'))

    def test_special_characters(self):
        """
        Special characters in the string.
        """
        self.assertEqual(u'abc-def-ghi', slugify(u'Abç \u0000 Def Ghi'))


class TestNumberedDirectoriesToGit(JigTestCase):

    """
    Utility for converting snapshots into Git repos.

    """
    def get_nd2g(self, name):
        """
        Gets a ``jig.tools.NumberedDirectoriesToGit`` object.

        Where ``name`` is the basename of a directory in
        :file:`src/jig/tests/fixtures/numbereddirs`.
        """
        nd = join(dirname(__file__), 'fixtures', 'numbereddirs', name)

        return NumberedDirectoriesToGit(nd)

    def get_group(self, name):
        """
        Gets a ``jig.tools.NumberedDirectoriesToGit`` from the group ``name``.

        Where ``name`` is the basename of a directory in
        :file:`src/jig/tests/fixtures/numbereddirs`.
        """
        return self.get_nd2g(name)

    def test_bad_directory(self):
        """
        Detects bad directory.
        """
        with self.assertRaises(ValueError):
            self.get_group('bad-directory')

    def test_add_one_file(self):
        """
        Adding one file.
        """
        repo = self.get_group('group-a').repo

        self.assertEqual(
            ['a.txt'],
            diff_tree(repo, 'HEAD^1')
        )

        # We added a second file
        self.assertEqual(
            ['b.txt'],
            diff_tree(repo, 'HEAD')
        )

    def test_modifying_one_file(self):
        """
        Modifying one file.
        """
        repo = self.get_group('group-b').repo

        self.assertTrue(repo)

        ## Start with one file
        #self.assertEqual(['a.txt'],
        #    [i.path for i in repo.commit('HEAD^1').tree])

        ## Same filename since it was modified
        #self.assertEqual(['a.txt'],
        #    [i.path for i in repo.commit('HEAD').tree])

        ## Should be a diff between them
        #diff = repo.commit('HEAD^1').diff('HEAD')

        #self.assertEqual('111\n', diff[0].a_blob.data_stream.read())
        #self.assertEqual('222\n', diff[0].b_blob.data_stream.read())

    def test_remove_one_file(self):
        """
        Removing one file.
        """
        repo = self.get_group('group-c')

        diff = repo.diffs()[1]

        # It's been removed
        self.assertEqual('b.txt', diff[0].a_blob.path)
        self.assertEqual(None, diff[0].b_blob)

    def test_adding_two_removing_two(self):
        """
        Adding two, removing two.
        """
        repo = self.get_group('group-d')

        diff = repo.diffs()[1]

        self.assertEqual('b.txt', diff[0].a_blob.path)
        self.assertEqual(None, diff[0].b_blob)

        self.assertEqual('c.txt', diff[1].a_blob.path)
        self.assertEqual(None, diff[1].b_blob)

        self.assertEqual(None, diff[2].a_blob)
        self.assertEqual('d.txt', diff[2].b_blob.path)

        self.assertEqual(None, diff[3].a_blob)
        self.assertEqual('e.txt', diff[3].b_blob.path)

    def test_add_one_modify_one_delete_one(self):
        """
        Add one, modify one, remove one.
        """
        repo = self.get_group('group-e')

        diff = repo.diffs()[1]

        # We modified a.txt
        self.assertEqual('a.txt', diff[0].a_blob.path)
        self.assertEqual('a\n', diff[0].a_blob.data_stream.read())
        self.assertEqual('aa\n', diff[0].b_blob.data_stream.read())

        # We removed b.txt
        self.assertEqual('b.txt', diff[1].a_blob.path)
        self.assertEqual(None, diff[1].b_blob)

        # And we added c.txt
        self.assertEqual(None, diff[2].a_blob)
        self.assertEqual('c.txt', diff[2].b_blob.path)

    def test_move_one_file(self):
        """
        Move one file.
        """
        repo = self.get_group('group-f')

        diff = repo.diffs()[1]

        self.assertEqual('a/b.txt', diff[0].a_blob.path)
        self.assertEqual(None, diff[0].b_blob)

        self.assertEqual(None, diff[1].a_blob)
        self.assertEqual('b/b.txt', diff[1].b_blob.path)

    def test_caches_repo(self):
        """
        Calling repo twice will return the same object.
        """
        nd2g = self.get_nd2g('group-a')

        self.assertEqual(id(nd2g.repo), id(nd2g.repo))

    def test_lots_of_changes(self):
        """
        Numerous changesets.
        """
        nd2g = self.get_nd2g('group-g')

        # Make sure we have the expected 5 commits
        self.assertEqual(5, len(list(nd2g.diffs())))


class TestIndent(JigTestCase):

    """
    The indent method will indent a sequence of strings.

    """
    def test_indent_string(self):
        """
        If the payload is a string it indents and returns a string.
        """
        self.assertEqual('    a', indent('a'))

    def test_indents_list(self):
        """
        List payload indents each item and returns a list.
        """
        self.assertEqual(
            [u'    a', u'    b', u'    c'],
            indent(['a', 'b', 'c']))

    def test_indents_different_by(self):
        """
        Can change the default indent of 4 to a different integer.
        """
        self.assertEqual(
            [u' a', u' b', u' c'],
            indent(['a', 'b', 'c'], by=1))

    def test_indents_different_character(self):
        """
        Can change the character used to indent to something else.
        """
        self.assertEqual(
            [u'?a', u'?b', u'?c'],
            indent(['a', 'b', 'c'], by=1, character='?'))
