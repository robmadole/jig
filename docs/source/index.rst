What is Jig
===========


Jig is a Git pre-commit hook on steroids. It abstracts some of the messier
manual bits away and lets you get down to business.

`Git Hooks`_ are little scripts that you can place in your ``$GIT_DIR/hooks``
directory to trigger actions at certain points. The ``pre-commit`` hook is
useful for performing actions right before Git writes a commit.

If you like to run linting tools like the `pep8 checker`_ or jslint_ or if you
want an automated way to make sure you didn't leave a ``debugger;`` line in you
JavaScript, Jig can help.

Jig comes with a set of common plugins that will probably be useful to you
right now, but the real goal is to make it easy for you to write your own.

Install it
----------

The Jig command line tool is written in Python and is available on PyPi. ::

    $ pip install jig || easy_install jig

Initialize a Git repository to use Jig
--------------------------------------

Let's test this out first with a new repository. ::

    $ mkdir gitrepo; cd $_
    $ git init .
    $ echo "Testing Jig" > README
    $ git add README; git commit -m 'First commit!'
    [master (root-commit) bc45fd3] First commit!
    1 files changed, 1 insertions(+), 0 deletions(-)
    create mode 100644 README

The repository has to be initialized to use Jig. It will create a ``.jig``
directory to hold configuration files. Jig also creates the ``pre-commit`` hook
for you automatically. Just point it at a Git repository and run this command:

::

    $ cd gitrepo
    $ jig init .
    Git repository has been initialized for use with jig.

Jig uses plugins to do the real work. It's empty to begin with so we'll install
a bundle of plugins now.

::

    $ jig plugin add http://github.com/robmadole/jig-plugins
    Added plugin pep8-checker in bundle jig-plugins to the repository.

Let's test our pep8-checker. `PEP8`_ is an endorsed style guide for writing
Python code. Johann Rocholl `created a tool`_ that checks for compliance.

Create a new file and put all of our imports on one line. This is contrary to PEP8.

::

    $ echo "import this; import that; import other" > myapp.py

Jig only works off the files you've staged for a commit.

::

    $ git add myapp.py

Use Git to create the commit and Jig will hop into action, running the
installed plugins for your repository.

::

    $ git commit -m 'Writing some hard to read Python code'
    ▾  pep8-checker

    ⚠  line 1: myapp.py
        import this; import that; import other
         - E702 multiple statements on one line (semicolon)

    Ran 1 plugin
        Info 0 Warn 1 Stop 0

    Commit anyway (hit enter), or "c" to cancel the commit

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
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _pep8 checker: http://pypi.python.org/pypi/pep8
.. _created a tool: `pep8 checker`_
.. _jslint: http://www.jslint.com/
