Jig on the command line
=======================

The command line tool is split into sub-commands.

**jig --help**

::

    usage: jig [-h] COMMAND

    optional arguments:
      -h, --help  show this help message and exit

    jig commands:
      init        Initialize a Git repository for use with Jig
      plugin      Manage jig plugins
      runnow      Run all plugins and show the results

    See `jig COMMAND --help` for more information

init
----

**jig init --help**

::

    usage: jig init [-h] [PATH]

    Initialize a Git repository for use with Jig

    positional arguments:
      path        Path to the Git repository

    optional arguments:
      -h, --help  show this help message and exit

The initialization process is quick and painless.

::

    $ mkdir gitrepo; cd $_
    $ git init .; jig init .
    Initialized empty Git repository in /Users/robmadole/gitrepo/.git/
    Git repository has been initialized for use with Jig.

If there is a pre-existing hook, Jig will not overwrite it.

::

    $ jig init .
    /Users/robmadole/gitrepo/.git/hooks/pre-commit already exists and we will not overwrite it. If you want to use jig you'll have to sort this out yourself.

runnow
------

**jig runnow --help**

::

    usage: jig runnow [-h] [PATH]

    Run all plugins and show the results

    positional arguments:
      path        Path to the Git repository

    optional arguments:
      -h, --help  show this help message and exit

Jig normally runs when you commit but you can force it to run as long as you
have some staged files.

plugin
------

**jig plugin --help**

::

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

**jig plugin list --help**

::

    usage: jig plugin list [-h] [-r] [PATH]

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

**jig plugin add --help**

::

    usage: jig plugin add [-h] [-r] URL|PATH

    positional arguments:
      plugin                URL or path to the plugin directory

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

Plugins can be added from URLs.

::

    $ jig plugin add http://github.com/robmadole/jig-plugins


Or from local filesystem.

::

    $ jig plugin add ./plugins/myplugin

You can also add more than one plugin at a time.

::

    $ jig plugin add ./plugins


**jig plugin remove --help**

::

    usage: jig plugin remove [-h] [-r] NAME [BUNDLE]

    positional arguments:
      name                  Plugin name
      bundle                Bundle name

    optional arguments:
      -h, --help            show this help message and exit
      --gitrepo PATH, -r PATH
                            Path to the Git repository, default current directory

Once a plugin is added, it can be easily removed.

::

    $ jig plugin remove myplugin

For information on ``create`` and ``test`` see :doc:`pluginapi`.
