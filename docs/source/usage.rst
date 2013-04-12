How to use Jig
==============

The following is a detailed step-by-step guide that takes you through:

#. creating a Git repository
#. configuring it to use Jig
#. installing some Jig plugins
#. running Jig

Create an empty Git repository
------------------------------

Let's test this out first with a new repository.

.. code-block:: console

    $ mkdir gitrepo; cd $_
    $ git init .

Create the root commit. Git repositories are not very useful without it.

.. code-block:: console

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

.. code-block:: console

    $ cd gitrepo
    $ jig init .
    Git repository has been initialized for use with Jig.

    You should tell Git to ignore the new .jig directory. Run this:

        $ echo ".jig" >> .gitignore

    Next install some plugins. Jig has a common set you may like:

        $ curl https://raw.github.com/robmadole/jig-plugins/lists/common.txt > .jigplugins.txt
        $ jig install .jigplugins.txt

If you're curious, you can :ref:`see what this thing has done
<development-plumbing>` to your repository.

Go ahead and ignore the ``.jig`` directory and we'll use that as our root
commit.

.. code-block:: console

    $ echo ".jig" >> .gitignore
    $ git add .gitignore
    $ git commit -m 'First commit'

Install some Jig plugins
------------------------

Jig uses "plugins" to do the real work. Your Jig config file (in
:file:`.jig/plugins.cfg`) is empty which means you have no plugins installed.

.. code-block:: console

    $ jig plugin add http://github.com/robmadole/jig-plugins@pep8-checker
    Added plugin pep8-checker in bundle jig-plugins to the repository.

    Run the plugins in the current repository with this command:

        $ jig runnow

    Jig works off of your staged files in the Git repository index.
    You place things in the index with `git add`. You will need to stage
    some files before you can run Jig.

Let's test our pep8-checker. `PEP8`_ is an endorsed style guide for writing
Python code. Johann Rocholl `created a tool`_ that checks for compliance.

Create a new file and put all of our imports on one line. This is contrary to
PEP8. How dreadful.

.. code-block:: console

    $ echo "import this; import that; import other" > myapp.py

Jig only works off the files you've staged for a commit.

.. code-block:: console

    $ git add myapp.py

Run Jig
-------

With our staged file, we're ready to commit.

.. code-block:: console

    $ git commit -m 'Writing some hard to read Python code'
    ▾  pep8-checker

    ⚠  line 1: myapp.py
        import this; import that; import other
         - E702 multiple statements on one line (semicolon)

       Jig ran 1 plugins
        Info 0 Warn 1 Stop 0

    Commit anyway (hit "c"), or stop (hit "s"):

Type :kbd:`c` and enter to commit anyway or :kbd:`s` to stop the commit,
giving you a chance to make changes.

Change plugin settings
----------------------

Plugins will sometimes have settings that you can configure. Edit the
:file:`.jig/plugins.cfg` and feel free to change how the plugins behave.

.. code-block:: ini
   :emphasize-lines: 3, 13

    [plugin:jig-plugins:pep8-checker]
    path = ../jig-plugins/pep8-checker
    default_type = warn

See information about the :ref:`types of messages <pluginapi-types>` that jig supports.

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
