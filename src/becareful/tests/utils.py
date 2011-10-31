from os.path import join, dirname

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
