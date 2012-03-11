What is Jig
===========

Jig is a Git pre-commit hook on steroids. It abstracts some of the messier
manual bits away and lets you get down to business.

`Git Hooks`_ are little scripts that you can place in your ``$GIT_DIR/hooks``
directory to trigger actions at certain points. The ``pre-commit`` hook is
useful for performing actions right before Git writes a commit.

Jig has a set of `common plugins`_ that will probably be useful to you
right now, but the real goal is to make it easy for you to write your own.

Jump straight to it
-------------------

* :doc:`Jig's command line tool <cli>`
* :doc:`Build your own Jig plugins <pluginapi>`

Install it
----------

The Jig command line tool is written in Python and is available on PyPi. ::

    $ pip install jig || easy_install jig

This is just a little shell trick that uses ``easy_install`` if it can't locate
``pip``.

Test drive
----------

Let's test this out first with a new repository. ::

    $ mkdir gitrepo; cd $_
    $ git init .

Create the root commit. Git repositories are not very useful without it.

::

    $ echo "Testing Jig" > README
    $ git add README; git commit -m 'First commit!'
    [master (root-commit) bc45fd3] First commit!
    1 files changed, 1 insertions(+), 0 deletions(-)
    create mode 100644 README

Jig will create the ``pre-commit`` hook for you automatically.  It will also
create a ``.jig`` directory to hold configuration files. Just point it at a Git
repository and run this command:

::

    $ cd gitrepo
    $ jig init .
    Git repository has been initialized for use with Jig.

If you're curious, you can :ref:`see what this thing has done
<development-plumbing>` to your repository.

Jig uses "plugins" to do the real work. Your Jig config file (in
:file:`.jig/plugins.cfg`) is empty which means you have no plugins installed.

::

    $ jig plugin add http://github.com/robmadole/jig-plugins
    Added plugin pep8-checker in bundle jig-plugins to the repository.
    Added plugin pyflakes in bundle jig-plugins to the repository.
    Added plugin whitespace in bundle jig-plugins to the repository.
    Added plugin whoops in bundle jig-plugins to the repository.

Let's test our pep8-checker. `PEP8`_ is an endorsed style guide for writing
Python code. Johann Rocholl `created a tool`_ that checks for compliance.

Create a new file and put all of our imports on one line. This is contrary to PEP8.

::

    $ echo "import this; import that; import other" > myapp.py

Jig only works off the files you've staged for a commit.

::

    $ git add myapp.py

See it in action
----------------

With our staged file, we're ready to commit.

::

    $ git commit -m 'Writing some hard to read Python code'
    ▾  pep8-checker

    ⚠  line 1: myapp.py
        import this; import that; import other
         - E702 multiple statements on one line (semicolon)

    Ran 1 plugin
        Info 0 Warn 1 Stop 0

    Commit anyway (hit enter), or "c" to cancel the commit

Jig isn't pushy. You can hit enter to commit anyway or :kbd:`c` cancels the
commit and gives you a chance to make changes.

In-depth docs
--------------

.. toctree::
   :maxdepth: 2

   cli
   pluginapi

Developer docs
--------------

.. toctree::
   :maxdepth: 2

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
