Hacking on Jig
==============

.. contents::

.. _development-plumbing:

Plumbing of Jig
---------------

How it hooks in
~~~~~~~~~~~~~~~

When you run :ref:`jig init <cli-init>` on a Git repository it does two basic things.

First it creates a :file:`$GIT_REPO/.git/hooks/pre-commit` file and makes it executable.

The file looks something like this:

::

    #!/usr/bin/python
    from sys import path
    from os.path import dirname, join

    # Make sure that we can find the directory that jig is installed
    # ... (various path modifications, don't look behind the curtain)

    from jig.runner import Runner

    # Start up the runner, passing in the repo directory
    jig = Runner()
    jig.fromhook(join(dirname(__file__), '..', '..'))

This is really just a redirection of control to the :py:class:`Runner` object.
It does all the work.

Secondly, it creates a :file:`$GIT_REPO/.jig` directory with a :file:`plugins`
directory and an empty :file:`plugins.cfg` configuration file within it.

As you :ref:`install plugins <cli-plugin-add>` the configuration file will get
modified to includes bits of information about whatever plugin you install.

When you install plugins from a URL, the plugin will be cloned for you
automatically and then placed in the :file:`.jig/plugins` directory.

If we installed the following plugin by running ``jig plugin install http://github.com/myusername/myplugin`` it would be saved in a directory similar to this.
:file:`.jig/plugins/24a8056749e448b182d44690a04ca0b7/myplugin`.

The configuration file :file:`plugins.cfg` will now contain a reference to this
location.

::

  [plugin:mybundle:myplugin]
  path = ./.jig/plugins/24a8056749e448b182d44690a04ca0b7/myplugin
  crank_widget = yes

It also contains the **default settings** for this plugin as defined by the
author. You can change these settings to affect the way the plugin behaves.

How it runs
~~~~~~~~~~~

Git automatically runs Jig when ``git commit`` is ran. It happens before your
staged files become an object in the Git database (before your commit is
written).

The neat part of this is that **if Jig returns an exit code of 0** the commit
will occur. But **if Jig returns a non-zero exit code like 1**, Git will abort the
commit.

Jig communicates with plugins using the `JSON`_ data format. Both the input and
the output are JSON. This is convenient because almost all scripting languages
that will likey be used to write Jig plugins can easily deal with JSON data.

A plugin has the ability to pass messages back to Jig that will be formatted
and displayed in the terminal.

.. image:: images/integration.png

Tests and coverage
------------------

Jig uses `Nose`_ to run tests and `coverage.py`_ to perform code coverage
analysis.

You need to have a cloned copy of Jig to run either one. You can start with a
read-only copy:

::

    $ git clone git://github.com/robmadole/jig.git

Or `fork the repository`_ on GitHub to make your own changes. The
:doc:`Jig License <license>` is friendly.

.. _development-buildout:

Jig also uses zc.buildout, which means you need to run a couple of commands to
download dependencies and create the scripts needed for development.

::

    $ python boostrap.py && ./bin/buildout

To run the tests:

::

    $ ./bin/jig-tests

To run test coverage:

::

    $ ./bin/jig-coverage

.. _Nose: http://readthedocs.org/docs/nose/en/latest/
.. _coverage.py: http://nedbatchelder.com/code/coverage/
.. _fork the repository: https://github.com/robmadole/jig/fork_select

Making the documentation
------------------------

This documentation is made with Sphinx_. To build the docs make sure you've ran
the :ref:`buildout <development-buildout>` first.


Build the HTML version:

::

    $ cd docs
    $ make html

The builds will be placed in :file:`build`.

.. _Sphinx: http://sphinx.pocoo.org/

.. _JSON: http://www.json.org/
