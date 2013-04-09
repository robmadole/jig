Jig on the command line
=======================

The command line tool is split into sub-commands.

.. contents::

Jig's help menu is available by running ``jig`` or ``jig --help``.

.. code-block:: console

    $ jig --help
    usage: jig [-h] COMMAND

    optional arguments:
      -h, --help  show this help message and exit

    jig commands:
      init        Initialize a Git repository for use with Jig
      plugin      Manage jig plugins
      runnow      Run all plugins and show the results

    See `jig COMMAND --help` for more information

.. _cli-init:

Initialize a Git repository to use Jig
--------------------------------------

Before Jig can be used on a Git repository, it must create the
:file:`$GIT_REPO/.git/hooks/pre-commit` hook and the :file:`$GIT_REPO/.jig`
directory.

This process is very similar to what Git itself does. Oddly enough the
sub-command is named the same.

.. code-block:: console

    $ jig init --help
    usage: jig init [-h] [PATH]

    Initialize a Git repository for use with Jig

    positional arguments:
      path        Path to the Git repository

    optional arguments:
      -h, --help  show this help message and exit

The initialization process is quick and painless.

.. code-block:: console

    $ mkdir gitrepo; cd $_
    $ git init .; jig init .
    Git repository has been initialized for use with Jig.

    You should tell Git to ignore the new .jig directory. Run this:

        $ echo ".jig" >> .gitignore

    Next install some plugins. Jig has a standard set you may like:

        $ jig plugin add http://github.com/robmadole/jig-plugins

    If there is a pre-existing hook, Jig will not overwrite it.

.. code-block:: console

    $ jig init .
    /Users/robmadole/gitrepo/.git/hooks/pre-commit already exists

    For Jig to operate automatically when you commit we need to create
    a new pre-commit hook.

    Check the existing pre-commit file and see if you are using it.

    If you do not need the existing pre-commit script, you can delete it
    and then run jig init again in this repository.

.. _cli-plugin:

Manage your plugins
-------------------

Jig is useless without plugins to perform some work. Plugins can do anything
the author chooses.

More than one plugin can be installed. They can be added or removed. You can
even use Jig to run :ref:`automated tests <pluginapi-testing>` on your plugins.

.. code-block:: console

    $ jig plugin --help
    usage: jig plugin [-h] ACTION

    Manage this repository's Jig plugins

    optional arguments:
      -h, --help            show this help message and exit

    actions:
      available commands to manage plugins

      {test,add,list,create,remove}
        list                list installed plugins
        add                 add a plugin
        remove              remove an installed plugin
        create              create a new plugin
        test                run a suite of plugin tests

.. _cli-plugin-list:

Listing installed plugins
~~~~~~~~~~~~~~~~~~~~~~~~~

To list all installed plugins use the following command. Any installed plugin
will be ran when the ``pre-commit`` hook or ``jig runnow`` is ran.

.. code-block:: console

    $ jig plugin list --help
    usage: jig plugin list [-h] [-r] [PATH]

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

Listing the plugin provides a quick summary like this:

.. code-block:: console

    $ jig plugin list
    Installed plugins

    Plugin name               Bundle name
    pep8-checker............. jig-plugins
    pyflakes................. jig-plugins
    whitespace............... jig-plugins
    woops.................... jig-plugins

    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.

.. _cli-plugin-add:

Adding plugins
~~~~~~~~~~~~~~

Jig doesn't pre-install anything for you. You have to explicitly add them.

.. code-block:: console

    $ jig plugin add --help
    usage: jig plugin add [-h] [-r GITREPO] URL|URL@BRANCH|PATH

    positional arguments:
      plugin                URL or path to the plugin directory, if URL you can
                            specify @BRANCHNAME to clone other than the default

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

Plugins can be added from Git URLs. If Jig detects that you've given it a URL
it will attempt to clone it.

.. note:: Right now Jig only supports cloning Git repositories. This may change
          in the future.

.. code-block:: console

    $ jig plugin add http://github.com/robmadole/jig-plugins


Or from local filesystem.

.. code-block:: console

    $ jig plugin add ./plugins/myplugin
    Added plugin myplugin in bundle mybundle to the repository.

You can also add more than one plugin at a time.

.. code-block:: console

    $ jig plugin add ./plugins
    Added plugin pep8-checker in bundle jig-plugins to the repository.
    Added plugin pyflakes in bundle jig-plugins to the repository.
    Added plugin whitespace in bundle jig-plugins to the repository.
    Added plugin woops in bundle jig-plugins to the repository.

    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.

.. _cli-plugin-update:

Updating plugins
~~~~~~~~~~~~~~~~

If you've installed plugins through a URL, you can update plugins which will
perform a ``git pull`` on each installed repository.

.. code-block:: console

    $ jig plugin update
    Updating plugins

    Plugin pep8-checker, woops, pyflakes, whitespace in bundle jig-plugins
        Total 1 (delta 1), reused 0 (delta 0)
        * refs/remotes/origin/master: fast forward to branch 'master'
          old..new: a1a0e8b..3c54ac6
        Updating a1a0e8b..3c54ac6
        Fast forward
         pep8-checker/pre-commit |    2 +-
         1 files changed, 1 insertions(+), 1 deletions(-)

.. note:: This only works if you've installed a plugin via a Git URL.

.. _cli-plugin-remove:

Removing plugins
~~~~~~~~~~~~~~~~

.. code-block:: console

    $ jig plugin remove --help
    usage: jig plugin remove [-h] [-r] NAME [BUNDLE]

    positional arguments:
      name                  Plugin name
      bundle                Bundle name

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

Once a plugin is added, it can be easily removed.

.. code-block:: console

    $ jig plugin remove myplugin
    Removed plugin myplugin

.. _cli-plugin-create:

Creating a plugin
~~~~~~~~~~~~~~~~~

The standard Jig plugins each have a single purpose and perform their role
well. However, you can probably think of at least one additional thing you'd
like Jig to do.

We encourage you to create your own plugins. A lot of work has gone into
structuring the plugins in such a way that they are intuitive to write and are
easy to test.

To help with this, an empty plugin can be created that functions as a great
starting point to write whatever you wish.

.. note:: Right now, Python is the only supported template. But plugins can be
          written in any scripting language installed on the system. We could use your
          help in writing :ref:`new pre-commit templates
          <pluginapi-pre-commit-templates>`.

.. code-block:: console

    $ jig plugin create --help
    usage: jig plugin create [-h] [-l TEMPLATE] [-d DIR] NAME BUNDLE

    positional arguments:
      name                  Plugin name
      bundle                Bundle name

    optional arguments:
      -h, --help            show this help message and exit
      --language TEMPLATE, -l TEMPLATE
                            Scripting language: python
      --dir DIR, -d DIR     Create in this directory

Plugins have a ``NAME`` and belong in a ``BUNDLE``. The name usually describes
what it does. The bundle can be a company, your name, or an identifier that
groups multiple plugins together.

Example of creating a plugin that checks widgets for the Acme Corporation.

.. code-block:: console

    $ jig plugin create widget-checker acme-corp
    Created plugin as ./widget-checker

The :doc:`plugin API <pluginapi>` has more information on where you can go
after you've created a new plugin.

.. _cli-plugin-test:

Running a plugin's tests
~~~~~~~~~~~~~~~~~~~~~~~~

Jig will run automated tests for a plugin if they exist.

For information on ``jig plugin test`` see :ref:`Testing Plugins <pluginapi-testing>`.

.. _cli-runnow:

Run Jig manually
----------------

Jig is normally ran before you commit. The primary purpose is to catch things
that you ordinarily wouldn't add.

But, there are occasions where you want to check your progress and run Jig and
all of your installed plugins without actually committing anything.

For this use case, ``runnow`` exists.

.. code-block:: console

    $ jig runnow --help
    usage: jig runnow [-h] [-p PLUGIN] [PATH]

    Run all plugins and show the results

    positional arguments:
      path                  Path to the Git repository

    optional arguments:
      -h, --help            show this help message and exit
      --plugin PLUGIN, -p PLUGIN
                            Only run this specific named plugin

When you call this command, Jig will perform the same motions that happen with
``git commit`` is ran.

.. code-block:: console

    $ jig runnow
    ▾  pep8-checker

    ⚠  line 1: a.py
        import foo; import bar; import daz;
         - E702 multiple statements on one line (semicolon)

    ▾  pyflakes

    ⚠  line 1: a.py
        'foo' imported but unused

    ⚠  line 1: a.py
        'bar' imported but unused

    ⚠  line 1: a.py
        'daz' imported but unused

    Ran 3 plugins
        Info 0 Warn 4 Stop 0
