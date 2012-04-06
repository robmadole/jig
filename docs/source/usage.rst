How to use Jig
==============

The following is a detailed step-by-step guide that takes you through:

#. creating a Git repository
#. configuring it to use Jig
#. installing some Jig plugins
#. running Jig

Create an empty Git repository
------------------------------

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

Configure it to use Jig
-----------------------

Jig will create the ``pre-commit`` hook for you automatically.  It will also
create a ``.jig`` directory to hold configuration files. Just point it at a Git
repository and run this command:

If you haven't, :ref:`install Jig now <install>`.

::

    $ cd gitrepo
    $ jig init .
    Git repository has been initialized for use with Jig.

If you're curious, you can :ref:`see what this thing has done
<development-plumbing>` to your repository.

Install some Jig plugins
------------------------

Jig uses "plugins" to do the real work. Your Jig config file (in
:file:`.jig/plugins.cfg`) is empty which means you have no plugins installed.

::

    $ jig plugin add http://github.com/robmadole/jig-plugins
    Added plugin pep8-checker in bundle jig-plugins to the repository.
    Added plugin pyflakes in bundle jig-plugins to the repository.
    Added plugin whitespace in bundle jig-plugins to the repository.
    Added plugin woops in bundle jig-plugins to the repository.

Let's test our pep8-checker. `PEP8`_ is an endorsed style guide for writing
Python code. Johann Rocholl `created a tool`_ that checks for compliance.

Create a new file and put all of our imports on one line. This is contrary to
PEP8. How dreadful.

::

    $ echo "import this; import that; import other" > myapp.py

Jig only works off the files you've staged for a commit.

::

    $ git add myapp.py

Run Jig
-------

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

What can the `common plugins`_ do besides check PEP8?

* Pyflakes - analyze Python files and check for various erros (written by the
  Divmod developers)
* Whitespace - look for lines with nothing but whitespace plus mixed tabs and
  spaces
* Woops - check for silly errors (like leaving a ``console.log(foo)`` in your
  JavaScript)

Change plugin settings
----------------------

Plugins will sometimes have settings that you can configure. Edit the
:file:`.jig/plugins.cfg` and feel free to change how the plugins behave.

.. code-block:: ini
    :emphasize-lines: 3, 13

    [plugin:jig-plugins:pep8-checker]
    path = ../jig-plugins/pep8-checker
    default_type = warn

    [plugin:jig-plugins:pyflakes]
    path = ../jig-plugins/pyflakes

    [plugin:jig-plugins:whitespace]
    path = ../jig-plugins/whitespace

    [plugin:jig-plugins:woops]
    path = ../jig-plugins/woops
    check_windows_newlines = yes

Write your own plugins
----------------------

Jig comes with a few useful plugins, but it's been designed to make plugin
creation easy.

It starts with this:

.. code-block:: console

    $ jig plugin create my-new-plugin my-company
    Created plugin as ./my-new-plugin

Edit :file:`my-new-plugin/pre-commit` and design it to perform whatever kind of
operation you like.

Then install it with:

.. code-block:: console

    $ jig plugin add my-new-plugin
    Added plugin my-new-plugin in bundle my-company to the repository.

Find out in detail :doc:`how to create a plugin <pluginapi>`.

.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _pep8 checker: http://pypi.python.org/pypi/pep8
.. _created a tool: `pep8 checker`_
.. _common plugins: http://github.com/robmadole/jig-plugins
