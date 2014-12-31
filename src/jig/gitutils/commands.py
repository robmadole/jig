import sh

try:
    # Default to no TTY for out
    sh.Command._call_args['tty_out'] = False

    assert sh.git
except sh.CommandNoFound:
    raise SystemExit(
        "Could not find an installation of Git "
        "anywhere on the path. Is Git installed?"
    )


def git(path=None):
    args = []
    kwargs = {'_tty_stdout': False}

    if path:
        args.extend(['-C', path])

    return sh.git.bake(*args, **kwargs)

git.error = sh.ErrorReturnCode

#add = git.add
#commit = git.commit
#config = git.config
#init = git.init
#log = git.log
#rev_list = getattr(git, 'rev-list')
#rev_parse = getattr(git, 'rev-parse')
#rm = git.rm
