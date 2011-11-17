from os.path import join, dirname
from unittest import TestCase

from becareful.tests.utils import NumberedDirectoriesToGit
from nose.plugins.attrib import attr


class TestNumberedDirectoriesToGit(TestCase):

    """
    Utility for converting snapshots into Git repos.

    """
    def get_group(self, name):
        """
        Gets a ``git.Repo`` from the group ``name``.

        Where ``name`` is the basename of a directory in
        :file:`src/becareful/tests/fixtures/numbereddirs`.
        """
        nd = join(dirname(__file__), 'fixtures', 'numbereddirs', name)

        return NumberedDirectoriesToGit(nd).get_repo()

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
        repo = self.get_group('group-a')

        self.assertEqual(['a.txt'],
            [i.path for i in repo.commit('HEAD^1').tree])

        # We added a second file
        self.assertEqual(['a.txt', 'b.txt'],
            [i.path for i in repo.commit('HEAD').tree])

    def test_modifying_one_file(self):
        """
        Modifying one file.
        """
        repo = self.get_group('group-b')

        # Start with one file
        self.assertEqual(['a.txt'],
            [i.path for i in repo.commit('HEAD^1').tree])

        # Same filename since it was modified
        self.assertEqual(['a.txt'],
            [i.path for i in repo.commit('HEAD').tree])

        # Should be a diff between them
        diff = repo.commit('HEAD^1').diff('HEAD')

        self.assertEqual('111\n', diff[0].a_blob.data_stream.read())
        self.assertEqual('222\n', diff[0].b_blob.data_stream.read())

    def test_remove_one_file(self):
        """
        Removing one file.
        """
        repo = self.get_group('group-c')

        diff = repo.commit('HEAD^1').diff('HEAD')

        # It's been removed
        self.assertEqual('b.txt', diff[0].a_blob.path)
        self.assertEqual(None, diff[0].b_blob)

    def test_adding_two_removing_two(self):
        """
        Adding two, removing two.
        """
        repo = self.get_group('group-d')

        diff = repo.commit('HEAD^1').diff('HEAD')

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

        diff = repo.commit('HEAD^1').diff('HEAD')

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

        diff = repo.commit('HEAD^1').diff('HEAD')

        self.assertEqual('a/b.txt', diff[0].a_blob.path)
        self.assertEqual(None, diff[0].b_blob)

        self.assertEqual(None, diff[1].a_blob)
        self.assertEqual('b/b.txt', diff[1].b_blob.path)

    def test_lots_of_changes(self):
        """
        Numerous changesets.
        """
        repo = self.get_group('group-g')

        # Make sure we have the expected 5 commits
        self.assertEqual(5, len(repo.iter_commits))
