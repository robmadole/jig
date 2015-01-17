from jig.packages.sh import sh

try:
    # Default to no TTY for out
    sh.Command._call_args['tty_out'] = False

    assert sh.git
except sh.CommandNotFound:   # pragma: no cover
    raise SystemExit(
        "Could not find an installation of Git "
        "anywhere on the path. Is Git installed?"
    )


def git(*args):
    shargs = []
    shkwargs = {'_tty_stdout': False}

    if args:
        shargs.extend(['-C', args[0]])

    return sh.git.bake(*shargs, **shkwargs)


def iter_raw_diff(path, *args, **kwargs):
    return git(path).diff(
        '--abbrev=40',
        '--full-index',
        '--color=never',
        '--word-diff=none',
        '--raw',
        *args,
        _iter=True,
        **kwargs
    )

git.error = sh.ErrorReturnCode
