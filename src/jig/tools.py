import re
from unicodedata import normalize
from os import listdir, walk, makedirs, chdir, getcwd
from os.path import join, dirname, isdir
from tempfile import mkdtemp
from shutil import copy2
from contextlib import contextmanager

from jig.gitutils.commands import git

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def _commit_hashes(repo):
    return git(repo).log(
        '--format=format:%H',
        '--no-decorate',
        '--no-color'
    )


def parent_of(commit):
    reachable = git()(
        'rev-list',
        '--skip=1',
        '--first-parent',
        commit
    ).splitlines()

    try:
        return reachable[0]
    except IndexError:
        return None


def slugify(text, delim=u'-'):
    """
    Generates a an ASCII-only slug.

    .. Author Armin Ronacher: http://flask.pocoo.org/snippets/5/
    """
    result = []
    for word in _punct_re.split(unicode(text).lower()):
        nword = normalize('NFKD', word).encode('ascii', 'ignore')
        if nword:
            # Filter out non-printable
            pword = ''.join([i for i in nword if ord(i) > 31])
            result.append(pword)
    return unicode(delim.join(filter(bool, result)))


def indent(payload, by=4, character=u' '):
    """
    Indents a sequence of strings with whitespace.

    By default it will indent by 4 spaces. Change the amount of indent with
    ``by`` and the character that is used with ``character``.

    Example:

        >>> print(indent(u'Jig', by=6, character=u'-'))
        ------Jig

    """
    return_first = False
    if isinstance(payload, (basestring)):
        payload = [payload]
        return_first = True

    indented = []
    for line in payload:
        indented.append(''.join([unicode(character)] * by) + unicode(line))

    if return_first:
        return indented[0]
    return indented


@contextmanager
def cwd_bounce(dir):
    """
    Temporarily changes to a directory and changes back in the end.

    Where ``dir`` is the directory you wish to change to. When the context
    manager exits it will change back to the original working directory.

    Context manager will yield the original working directory and make that
    available to the context manager's assignment target.
    """
    original_dir = getcwd()

    try:
        chdir(dir)

        yield original_dir
    finally:
        chdir(original_dir)


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
    you'd expect in a testing utility for creating Git repo fixtures.

    """
    def __init__(self, numdir):
        if not isdir(numdir):
            raise ValueError('Not a directory: {0}.'.format(numdir))

        self.numdir = numdir
        self.target = mkdtemp()
        self._repo = None

    @property
    def repo(self):
        """
        Does the conversion and returns the ``git.Repo`` object.
        """
        if not self._repo:
            git().init(self.target)

            self._repo = self.target

            for d in sorted(listdir(self.numdir)):
                self._commit(self._repo, join(self.numdir, d))

        return self._repo

    def diffs(self):
        """
        Get a list of diffs for all commits.
        """
        repo = self.repo

        raise NotImplementedError()

        diffs = []
        for commit in _commit_hashes(repo).splitlines():
            try:
                parent = parent_of(commit)
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
            repo, strip=self.target))

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

            git(repo).add(path)

        # Delete
        for path in paths_to_del:
            git(repo).rm(path)

        git(repo).commit('-m', 'Commit from numbered directory {0}'.format(d))

    def _flattendirectory(self, d, strip=None):
        """
        Recursively generates a list of paths from a directory.

        If ``strip`` is not provided it defaults to ``d``.
        """
        for (dirpath, _dirname, filenames) in walk(d):
            for fn in filenames:
                sdir = dirpath.replace('{0}'.format(strip), '').lstrip('/')
                if sdir.startswith('.git'):
                    continue
                yield join(sdir, fn)
