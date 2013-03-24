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

Install some Jig plugins.

.. code-block:: console

    $ jig plugin add http://github.com/robmadole/jig-plugins
    Added plugin jshint in bundle jig-plugins to the repository.
    Added plugin pep8-checker in bundle jig-plugins to the repository.
    Added plugin pyflakes in bundle jig-plugins to the repository.
    Added plugin whitespace in bundle jig-plugins to the repository.
    Added plugin woops in bundle jig-plugins to the repository.

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

    Commit anyway (hit enter), or "c" to cancel the commit

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

License
-------

Jig is licensed under a :doc:`BSD license <license>`.


.. _Git Hooks: http://book.git-scm.com/5_git_hooks.html
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _pep8 checker: http://pypi.python.org/pypi/pep8
.. _created a tool: `pep8 checker`_
.. _jslint: http://www.jslint.com/
.. _common plugins: http://github.com/robmadole/jig-plugins
