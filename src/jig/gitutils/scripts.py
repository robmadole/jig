from textwrap import dedent

RUN_JIG_SCRIPT = \
    dedent("""\
    #!{python_executable}
    from sys import path
    from os.path import dirname, join

    # Make sure that we can find the directory that jig is installed
    path.append('{jig_dir}')
    path.append('{gitdb_dir}')

    from jig.runner import Runner

    # Start up the runner, passing in the repo directory
    jig = Runner()
    jig.fromhook(join(dirname(__file__), '..', '..'))
    """).strip()

AUTO_JIG_INIT_SCRIPT = \
    dedent("""\
    #!{python_executable}
    from sys import path, exit, stderr, stdout
    from os.path import dirname, realpath
    from os import unlink, environ
    from subprocess import check_call, CalledProcessError

    # Figure out where the Git directory is
    git_directory = realpath(environ.get('GIT_DIR', '.git'))
    repository_directory = dirname(git_directory)

    # Remove this pre-commit script
    unlink(__file__)

    stdout.write(u'Jig auto-install is beginning...\\n\\n')
    stdout.flush()

    try:
        check_call(u'jig init {{0}}'.format(repository_directory), shell=True)
    except (OSError, CalledProcessError) as e:
        stderr.write(
            u'Initialization of Jig failed so we are disabling\\n'
            u'the auto-install process. You need to manually install\\n'
            u'jig to use it.\\n'
        )
    else:
        stdout.write(
            u'\\nAfter you\\'ve installed some plugins run git commit again.\\n'
        )

    # Exit with non-zero so the commit can be checked with the real Jig
    # the next time a commit is attempted.
    exit(1)
    """).strip()
