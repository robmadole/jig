What is Jig
===========

Jig is a Git pre-commit hook on steroids. It abstracts some of the messier
bits away and lets you get down to business.

`Git Hooks`_ are little scripts that you can place in your ``$GIT_DIR/hooks``
directory to trigger actions at certain points. The ``pre-commit`` hook is
useful for performing actions right before Git writes a commit.

If you like to run linting tools like `pep8`_ or `jslint`_ or if you just want to have
an automated way to make sure you didn't leave a ``debugger;`` line in you
script, Jig can help.

Jig comes with a set of common plugins that will probably be useful to you
right now, but the real goal is to make it easy for you to develop your own.

Install it
----------

Jig is written in Python and is available on PyPi. ::

    pip install jig

Initialize a Git repository to use Jig
--------------------------------------

Jig can create the ``pre-commit`` hook for you automatically. Just point it at
a Git repository and run this command ::

    $ cd gitrepo
    $ jig init .

¨

In-depth docs:
--------------

.. toctree::
   :maxdepth: 2

   pluginapi

Development documentation:

.. toctree::
   :maxdepth: 1

   devapi

.. _Git Hooks: http://book.git-scm.com/5_git_hooks.html
.. _pep8: http://pypi.python.org/pypi/pep8
.. _jslint: http://www.jslint.com/
