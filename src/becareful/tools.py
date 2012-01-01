import re
from unicodedata import normalize
from os import listdir, walk, makedirs, unlink
from os.path import join, dirname, isdir
from tempfile import mkdtemp
from shutil import copy2

from git import Repo

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """
    Generates a an ASCII-only slug.

    .. Author Armin Ronacher: http://flask.pocoo.org/snippets/5/
    """
    result = []
    for word in _punct_re.split(unicode(text).lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))


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
        self._repo = None

    @property
    def repo(self):
        """
        Does the conversion and returns the ``git.Repo`` object.
        """
        if not self._repo:
            self._repo = Repo.init(self.target)

            for d in sorted(listdir(self.numdir)):
                self._commit(self._repo, join(self.numdir, d))

        return self._repo

    def diffs(self):
        """
        Get a list of diffs for all commits.
        """
        repo = self.repo

        diffs = []
        for commit in repo.iter_commits():
            try:
                diffs.append(commit.parents[0].diff(commit))
            except IndexError:
                pass

        # Make the oldest first
        diffs.reverse()

        return diffs

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
