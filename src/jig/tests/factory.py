from jig.tests.mocks import MockPlugin

try:
    from collections import OrderedDict
except ImportError:   # pragma: no cover
    from ordereddict import OrderedDict

anon_obj = object()


def error():
    return OrderedDict([
        (MockPlugin(), (1, '', 'Plugin failed'))
    ])


def no_results():
    return OrderedDict([
        (MockPlugin(), (0, None, '')),
        (MockPlugin(), (0, '', '')),
        (MockPlugin(), (0, [''], '')),
        (MockPlugin(), (0, [['w', '']], '')),
        (MockPlugin(), (0, {u'a.txt': u''}, '')),
        (MockPlugin(), (0, {u'a.txt': [[]]}, '')),
        (MockPlugin(), (0, {u'a.txt': [[u'']]}, '')),
        (MockPlugin(), (0, {u'a.txt': [['', u'']]}, '')),
        (MockPlugin(), (0, {u'a.txt': [[None, '', u'']]}, '')),
        (MockPlugin(), (0, {u'a.txt': [[1, '', u'']]}, ''))
    ])


def commit_specific_message():
    return OrderedDict([
        (MockPlugin(), (0, 'default', '')),
        (MockPlugin(), (0, [[u'warn', u'warning']], ''))
    ])


def file_specific_message():
    # Line number of None will be recognized as file-specific.
    stdout1 = OrderedDict([
        (u'a.txt', [[None, u'warn', 'Problem with this file']])
    ])

    # Will a length of 2 be recognized as file-specific?
    stdout2 = OrderedDict([
        (u'a.txt', [[u'warn', 'Problem with this file']])
    ])

    # Can we handle more than one file and different argument signatures
    # for the type?
    stdout3 = OrderedDict([
        (u'a.txt', [['Info A']]),
        (u'b.txt', [[u'warn', 'Warn B']]),
        (u'c.txt', [[u's', 'Stop C']])
    ])

    return OrderedDict([
        (MockPlugin(), (0, stdout1, '')),
        (MockPlugin(), (0, stdout2, '')),
        (MockPlugin(), (0, stdout3, ''))
    ])


def line_specific_message():
    stdout = OrderedDict([
        (u'a.txt', [[1, None, 'Info A']]),
        (u'b.txt', [[2, u'warn', 'Warn B']]),
        (u'c.txt', [[3, u'stop', 'Stop C']])
    ])

    return OrderedDict([
        (MockPlugin(), (0, stdout, ''))
    ])


def one_of_each():
    return OrderedDict([
        (MockPlugin(), (0, ['C'], '')),
        (MockPlugin(), (0, {u'a.txt': u'F'}, '')),
        (MockPlugin(), (0, {u'a.txt': [[1, None, u'L']]}, ''))
    ])


def commit_specific_error():
    return OrderedDict([
        (MockPlugin(), (0, anon_obj, '')),
        (MockPlugin(), (0, [[1, 2, 3, 4, 5]], ''))
    ])


def file_specific_error():
    return OrderedDict([
        (MockPlugin(), (0, {'a.txt': anon_obj}, '')),
        (MockPlugin(), (0, {'a.txt': [anon_obj]}, '')),
        (MockPlugin(), (0, {'a.txt': [1,  None]}, '')),
        (MockPlugin(), (0, {'a.txt': [[1, 2, 3, 4, 5]]}, ''))
    ])
