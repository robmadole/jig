from textwrap import dedent


def _hint(hint):
    return [u''] + dedent(hint).strip().splitlines()

AFTER_INIT = _hint(
    u"""
    You should tell Git to ignore the new .jig directory. Run this:

        $ echo ".jig" >> .gitignore

    Next install some plugins. Jig has a standard set you may like:

        $ jig plugin add http://github.com/robmadole/jig-plugins
    """)

PRE_COMMIT_EXISTS = _hint(
    u"""
    For Jig to operate automatically when you commit we need to create
    a new pre-commit hook.

    Check the existing pre-commit file and see if you are using it.

    If you do not need the existing pre-commit script, you can delete it
    and then run jig init again in this repository.
    """)

NOT_GIT_REPO = _hint(
    u"""
    To initialize a directory for use with Git, run:

        $ git init [directory]

    After you do this you can try your Jig command again.
    """)

GIT_REPO_NOT_INITIALIZED = _hint(
    u"""
    To use Jig you must first make sure the directory has been
    initialized for use with Git.

    Make sure you run this first:

        $ git init [directory]

    Then run the init command using Jig:

        $ jig init [directory]
    """)

ALREADY_INITIALIZED = _hint(
    u"""
    You are initializing a Git repository for use with Jig but it
    seems this has already been done.

    If you need to re-initialize for some reason you can manually remove
    the .jig directory in the root of the repository. This is probably not
    necessary and will delete all your settings and installed plugins.
    """)

NO_PLUGINS_INSTALLED = _hint(
    u"""
    You can install plugins by running:

        $ jig plugin add URL|URL@BRANCH|PATH

    There is a standard set available you can try:

        $ jig plugin add http://github.com/robmadole/jig-plugins
    """)

USE_RUNNOW = _hint(
    u"""
    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.
    """)

FORK_PROJECT_GITHUB = _hint(
    u"""
    You can fork this project on GitHub.

    http://github.com/robmadole/jig
    """)
