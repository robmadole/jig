from textwrap import dedent


def _hint(hint):
    return u'\n' + dedent(hint).strip()

AFTER_INIT = _hint(
    u"""
    You should tell Git to ignore the new .jig directory. Run this:

        $ echo ".jig" >> .gitignore

    Next install some plugins. Jig has a common set you may like:

        $ curl https://raw.github.com/robmadole/jig-plugins/lists/common.txt > .jigplugins.txt
        $ jig install .jigplugins.txt
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

GIT_REV_LIST_FORMAT_ERROR = _hint(
    u"""
    The revision range is not in a valid format.

    Use "REV_A..REV_B" to specify the revisions that Jig should operate against.
    """)

GIT_REV_LIST_MISSING = _hint(
    u"""
    The revision specified is formatted correctly but one of both of the revisions
    could not be found.
    """)

GIT_TEMPLATES_MISSING = _hint(
    u"""
    Jig looks for the shared Git templates in /usr/share and /usr/local. You may
    have a non-standard installation of Git.
    """)

GIT_HOME_TEMPLATES_EXISTS = _hint(
    u"""
    You may have already configured Jig for this. Delete the directory
    and run the command again if you are sure this is what you want to
    do.
    """)

INIT_TEMPLATE_DIR_ALREADY_SET = _hint(
    u"""
    Your Git config already has a value set for init.templatedir. Jig will not
    change this because you have probably done this for a reason. If you'd like
    to use hooks from Jig you can manually copy them from ~/.jig/git/templates/hooks.
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
    You can add plugins one at a time by running:

        $ jig plugin add URL|URL@BRANCH|PATH

    You can also install a list of plugins from a file:

        $ curl https://raw.github.com/robmadole/jig-plugins/lists/common.txt > .jigplugins.txt
        $ jig install .jigplugins.txt

    It's a good idea to add .jigplugins.txt to your Git repository after you are done.
    """)

USE_RUNNOW = _hint(
    u"""
    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.
    """)

CHANGE_PLUGIN_SETTINGS = _hint(
    u"""
    Plugin settings can be changed with the following command:

        $ jig config set BUNDLE.PLUGIN.KEY VALUE

    BUNDLE is the bundle name of an installed plugin
    PLUGIN is the name of an installed plugin.
    KEY is the name/key of the setting.
    VALUE is the desired value for the KEY.
    """)

FORK_PROJECT_GITHUB = _hint(
    u"""
    You can fork this project on GitHub.

    http://github.com/robmadole/jig
    """)

INVALID_RANGE = _hint(
    u"""
    Ranges are formatted as a number followed by two dots and another number.
    The first number specifies the start of the range. The second number
    specifies the end.

    To specify a range between 1 and 2 you would use "1..2".

    You can also specify larger ranges like "3..7"
    """)

INVALID_CONFIG_KEY = _hint(
    u"""
    Config keys must be in the following format:

    BUNDLE.PLUGIN.SETTING

    For example, if a plugin named "doublecheck" was installed from a bundle named
    "acme" the config key would be something like:

    acme.doublecheck.ignore_widgets

    For a full list of settings:

        $ jig config list
    """)
