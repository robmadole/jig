from os import listdir, walk, makedirs, unlink
from os.path import join, dirname, isdir
from tempfile import mkdtemp
from shutil import copy2

from git.test.lib import StringProcessAdapter
from git import Repo, Diff


def diffindexfrom(basename):
    """
    Creates a :py:class:`git.diff.DiffIndex` object from a fixture.

    ``basename`` should be the name of a file in the
    :file:`src/becareful/tests/fixtures` directory.
    """
    filename = join(dirname(__file__), 'fixtures', 'diffs', basename)
    with open(filename, 'r') as fh:
        data = fh.read()

    spa = StringProcessAdapter(data)
    repo = Repo(join(dirname(__file__), 'fixtures', 'repo01'))
    diffs = Diff._index_from_patch_format(repo, spa.stdout)

    return diffs


class NumberedDirectoriesToGit(object):

    """
    Converts a directory listing of snapshots to a Git repository.

    Given a directory where the layout is this::

        $ ls -1 testrepo
        .
        ..
        01
        02
        03

    This object can be initialized like this::

        >>> repo = NumberedDirectoriesToGit('testrepo')

    The resulting object will be a GitPython ``git.Repo`` object where each
    commit corresponds to the numbered directory. Commit 1 will be the contents
    in `01`. Commit 2 will be the contents of `02`, etc.

    The easiest way to think about this is in terms of using ``git checkout``.
    Each directory is a snapshot of the detached head for that commit.

    Supports directories, deleting files, and file modifications. Everything
    you'd expect in a testing utility for create Git repo fixtures.

    """
    def __init__(self, numdir):
        if not isdir(numdir):
            raise ValueError('Not a directory: {}'.format(numdir))

        self.numdir = numdir
        self.target = mkdtemp()

    def get_repo(self):
        """
        Does the conversion and returns the ``git.Repo`` object.
        """
        repo = Repo.init(self.target)

        for d in sorted(listdir(self.numdir)):
            self._commit(repo, join(self.numdir, d))

        return repo

    def _commit(self, repo, d):
        """
        Creates a new commit in the repository

        Where ``repo`` is a ``git.Repo`` object to create the commit in. And
        ``d`` is the directory you want the new commit to look like once the
        commit has been made.
        """
        # List files currently in our repository
        paths_current = set(self._flattendirectory(
            repo.working_dir, strip=self.target))

        # What needs to be added
        paths_new = set(self._flattendirectory(
            d, strip=d))

        paths_to_add = paths_new - paths_current
        paths_to_del = paths_current - paths_new
        paths_same = paths_new.intersection(paths_current)

        # Add
        for path in paths_to_add.union(paths_same):
            # Create the directory if needed
            directory = join(self.target, dirname(path))
            if not isdir(directory):
                makedirs(directory)

            copy2(
                join(d, path),
                join(self.target, path))

            repo.index.add([path])

        # Delete
        for path in paths_to_del:
           repo.index.remove([join(self.target, path)])

           unlink(join(self.target, path))

        repo.index.commit('Commit from numbered directory {}'.format(d))

    def _flattendirectory(self, d, strip=None):
        """
        Recursively generates a list of paths from a directory.

        If ``strip`` is not provided it defaults to ``d``.
        """
        if not strip:
            strip = d

        for (dirpath, dirname, filenames) in walk(d):
            for fn in filenames:
                sdir = dirpath.replace('{}'.format(strip), '').lstrip('/')
                if sdir.startswith('.git'):
                    continue
                yield join(sdir, fn)
