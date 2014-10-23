What is Jig
===========

**Jig is a Git pre-commit hook on steroids**.

`Git Hooks`_ are little scripts that you can place in your ``$GIT_DIR/hooks``
directory to trigger actions at certain points. The ``pre-commit`` hook is
useful for performing actions right before Git writes a commit.

Jig is a command line tool as well as a utility for creating and running "plugins".

It has a set of `common plugins`_ that will probably be useful to you
right now, but the real goal is to make it easy for you to write your own.

.. _install:

Install it
----------

The Jig command line tool is written in Python and is available on PyPi.

.. code-block:: console

    $ pip install jig || easy_install jig

This is just a little shell trick that uses ``easy_install`` if it can't locate
``pip``.

Jig currently supports Python 2.6 and Python 2.7.

Test drive
----------

Change directories into your Git repository and initialize it to use Jig.

.. code-block:: console

    $ cd myrepo
    $ jig init .
    Git repository has been initialized for use with Jig.

    You should tell Git to ignore the new .jig directory. Run this:

        $ echo ".jig" >> .gitignore

    Next install some plugins. Jig has a common set you may like:

        $ curl https://raw.github.com/robmadole/jig-plugins/lists/common.txt > .jigplugins.txt
        $ jig install .jigplugins.txt

Create a file that lists the plugins you'd like to install.

.. code-block:: console

    $ curl https://raw.github.com/robmadole/jig-plugins/lists/common.txt > .jigplugins.txt
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    97  100    97    0     0    144      0 --:--:-- --:--:-- --:--:--   425

Install the Jig plugins.

.. code-block:: console

    $ jig install .jigplugins.txt
    From http://github.com/robmadole/jig-plugins@whitespace:
     - Added plugin whitespace in bundle jig-plugins
    From http://github.com/robmadole/jig-plugins@woops:
     - Added plugin woops in bundle jig-plugins

    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.

Stage some changes and then commit.

.. code-block:: console

    $ git add mylib.py

Jig will run and let you know if it catches anything.

.. code-block:: console

    $ git commit -m 'Adding my awesome new library'
    ▾  woops

    ⚠  line 23: mylib.py
        print statement

    Ran 1 plugin
        Info 0 Warn 1 Stop 0

    Commit anyway (hit "c"), or stop (hit "s"):

Where to go next
----------------

.. toctree::
   :maxdepth: 2

   usage
   pluginapi

In-depth docs
--------------

.. toctree::
   :maxdepth: 2

   cli
   devapi

Change log
----------

.. include:: ../../NEWS.rst
   :start-line: 3

License
-------

Jig is licensed under a :doc:`BSD license <license>`.


.. _Git Hooks: http://git-scm.com/book/en/Customizing-Git-Git-Hooks
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _pep8 checker: http://pypi.python.org/pypi/pep8
.. _created a tool: `pep8 checker`_
.. _jslint: http://www.jslint.com/
.. _common plugins: http://github.com/robmadole/jig-plugins
