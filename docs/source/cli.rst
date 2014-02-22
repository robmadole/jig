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
      config      Manage settings for installed Jig plugins
      init        Initialize a Git repository for use with Jig
      install     Install a list of Jig plugins from a file
      plugin      Manage this repository's Jig plugins
      report      Run plugins on a revision range
      runnow      Run plugins on staged changes and show the results
      sticky      Make Jig auto-init every time you git clone
      version     Show Jig's version number

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
    Initialized empty Git repository in /Users/robmadole/gitrepo/.git/
    Git repository has been initialized for use with Jig.

    You should tell Git to ignore the new .jig directory. Run this:

        $ echo ".jig" >> .gitignore

    Next install some plugins. Jig has a common set you may like:

        $ curl https://raw.github.com/robmadole/jig-plugins/lists/common.txt > .jigplugins.txt
        $ jig install .jigplugins.txt

If there is a pre-existing hook, Jig will not overwrite it.

.. code-block:: console

    $ jig init .
    /Users/robmadole/gitrepo/.git/hooks/pre-commit already exists

    For Jig to operate automatically when you commit we need to create
    a new pre-commit hook.

    Check the existing pre-commit file and see if you are using it.

    If you do not need the existing pre-commit script, you can delete it
    and then run jig init again in this repository.


.. _cli-sticky:

Have Jig auto-init every time you clone
---------------------------------------

Calling ``jig init`` on every newly cloned repository can become tedious and there
is a chance that you will forget to do it.

Jig can modify your Git ``init.templatedir`` setting for you and automatically run
``jig init`` when you clone or initialize a Git repository.

This is referred to as "sticky" mode. To set this up:

.. code-block:: console

    $ jig sticky
    Jig has been setup to run everytime you clone.

.. hint:: Jig is cautious about making modifications to your ~/.gitconfig. It
          will refuse to change the init.templatedir setting if you've already
          set this previous to running the ``sticky`` command.

.. _cli-plugin:

Install a list of plugins from a file
-------------------------------------

Jig is useless without plugins to perform some work. Plugins can do anything
the author chooses.

Plugins can be installed one at a time or from a file that lists each of many
plugins. They can be added or removed. You can even use Jig to run
:ref:`automated tests <pluginapi-testing>` on your plugins.

To install from a file you use the ``jig install`` command.

.. hint:: To find some handy examples of plugins that are useful based on the
          type of project you have, checkout https://github.com/robmadole/jig-plugins/tree/lists

.. _cli-install:

.. code-block:: console

    $ jig install -h
    usage: jig install [-h] [-r GITREPO] [PLUGINSFILE]

    Install a list of Jig plugins from a file

    positional arguments:
      pluginsfile           Path to a file containing the location of plugins to
                            install, each line of the file should contain
                            URL|URL@BRANCH|PATH

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

For this example we can start with an example Python project list.

.. code-block:: console

    $ curl https://raw.github.com/robmadole/jig-plugins/lists/python.txt > .jigplugins.txt

After this is downloaded you can see that each line simply points to a specific
plugin.

.. code-block:: console

    $ cat .jigplugins.txt
    http://github.com/robmadole/jig-plugins@pep8-checker
    http://github.com/robmadole/jig-plugins@pyflakes
    http://github.com/robmadole/jig-plugins@woops
    http://github.com/robmadole/jig-plugins@whitespace

Install the plugins:

.. code-block:: console

    $ jig install .jigplugins.txt
    From http://github.com/robmadole/jig-plugins@pep8-checker:
     - Added plugin pep8-checker in bundle jig-plugins
    From http://github.com/robmadole/jig-plugins@pyflakes:
     - Added plugin pyflakes in bundle jig-plugins
    From http://github.com/robmadole/jig-plugins@woops:
     - Added plugin woops in bundle jig-plugins
    From http://github.com/robmadole/jig-plugins@whitespace:
     - Added plugin whitespace in bundle jig-plugins

    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.

Manage your plugins
-------------------

To install just one plugin or otherwise work with existing plugins, your the
``jig plugin`` command.

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
    usage: jig plugin list [-h] [-r]

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

.. _cli-config:

Plugin settings
---------------

Each plugin can have settings that change the way they behave. For example, the
pep8-checker plugin allows you to turn off the E501 reporting which tells you
that a line is longer than 80 characters (a very common thing for Python
developers to ignore).

.. code-block:: console

    $ jig config --help
    usage: jig config [-h] ACTION

    Manage settings for installed Jig plugins

    optional arguments:
      -h, --help  show this help message and exit

    actions:
      available commands to manage settings

      {list,set}
        list      list all settings
        set       set a single setting for an installed plugin

.. _cli-config-list:

List the current settings
~~~~~~~~~~~~~~~~~~~~~~~~~

To list the current settings, use the ``jig config list`` command.

The command only works if you've already :ref:`installed some plugins
<cli-plugin-add>`.

.. code-block:: console

    # jig config list --help
    usage: jig config list [-h] [-r GITREPO]

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

If the pep8-checker plugin was installed, the settings may look something like
this:

.. code-block:: console
   :emphasize-lines: 1,2

    jig-plugins.pep8-checker.default_type=warn
    jig-plugins.pep8-checker.report_e501=yes

    Plugin settings can be changed with the following command:

        $ jig config set BUNDLE.PLUGIN.KEY VALUE

    BUNDLE is the bundle name of an installed plugin
    PLUGIN is the name of an installed plugin.
    KEY is the name/key of the setting.
    VALUE is the desired value for the KEY.

.. _cli-config-set:

Change a setting
~~~~~~~~~~~~~~~~

Settings are changed one at a time.

.. code-block:: console

    $ jig config set --help
    usage: jig config set [-h] [-r GITREPO] KEY VALUE

    positional arguments:
      key                   Setting key which is a dot-separated string of the
                            bundle name, plugin name, and setting name
      value                 Value for the specified settings

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

The ``KEY`` is a dot-separated string consisting of:

#. Bundle name
#. followed by plugin name
#. followed by setting key

If we take the pep8-checker example, to turn off E501 reporting we would run
this command:

.. code-block:: console

    $ jig config set jig-plugins.pep8-checker.report_e501 no

.. _cli-config-about:

Settings help
~~~~~~~~~~~~~

Sometimes it's not immediately apparent what a setting's purpose is from it's
key. Plugin developers are encouraged to write help messages.

List the help messages, if available:

.. code-block:: console

    $ jig config about
    jig-plugins.pep8-checker.default_type
    (default: warn)
       When an error is found, use this type of Jig message to communicate
       it. One of: info, warn, stop.

    jig-plugins.pep8-checker.report_e501
    (default: yes)
       Report lines with greater than 80 characters? Either yes or no.

.. _cli-runnow:

Run Jig manually
----------------

Jig is normally ran before you commit using Git's pre-commit hook.

But, there are occasions where you want to check your progress and run Jig and
all of your installed plugins without actually committing anything.

For this case, the ``runnow`` command exists.

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

If you only want to run a specific plugin, use the ``--plugin`` option.

.. code-block:: console

    $ jig runnow --plugin pyflakes
    ▾  pyflakes

    ⚠  line 1: a.py
        'foo' imported but unused

    ⚠  line 1: a.py
        'bar' imported but unused

    ⚠  line 1: a.py
        'daz' imported but unused

    Ran 1 plugins
        Info 0 Warn 3 Stop 0

.. _cli-report:

Run Jig on a given revision range
---------------------------------

Jig can also be ran on a list of previous commits instead of just on the changes
that are staged in Git's index.

Use the ``report`` command.

.. code-block:: console

    $ jig report --help
    usage: jig report [-h] [-p PLUGIN] [--rev-range REVISION_RANGE] [PATH]

    Run plugins on a revision range

    positional arguments:
      path                  Path to the Git repository

    optional arguments:
      -h, --help            show this help message and exit
      --plugin PLUGIN, -p PLUGIN
                            Only run this specific named plugin
      --rev-range REV_RANGE
                            Git revision range to run the plugins against

The range is assumed to be the most recent commit but you can change that with
the ``--rev-range`` option.  This needs to be formatted as ``REV_A..REV_B``
with the double dots (``..``) to separate the first and second commit in the
range.

.. code-block:: console

    $ jig report --rev-range origin/master..report-command
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

This command also supports the ``--plugin`` option and works the same way as :ref:`runnow <cli-runnow>`
