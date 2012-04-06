Plugin API
==========

Jig by itself is useless. You need "plugins" to do the work.

The following documentation outlines what it takes to build plugins.

One of the primary reasons Jig exists is to enable you to write your own.

.. _pluginapi-anatomy:

The anatomy of a plugin
-----------------------

The most basic plugin has just two files:

* pre-commit
* config.cfg

(Wait, don't run off and try to create these yet. The :doc:`Jig command line tool <cli>`
will do this for you. Read on.)

The :file:`pre-commit` is your script and :file:`config.cfg` contains info about your plugin.

It will recieve JSON data through the ``stdin`` stream. It's expected to write
to ``stdout`` if it has anything to say (or ``stderr`` if it runs into
problems). Although a plugin doesn't have to write anything.

The :file:`config.cfg` file contains the plugin name and bundle. It
can also contain default settings but they aren't required.

Here's an example:

::

    [plugin]
    bundle = mybundle
    name = myplugin

    [settings]

.. note:: If you plan on making more than one plugin and you'd like to keep
          them grouped together, keep the ``bundle`` identifier the same.

If you want to add settings to your plugin which can be read by your ``pre-commit`` script, you can do that like this:

::

    [plugin]
    bundle = mybundle
    name = myplugin

    [settings]
    verbose = no
    foo = bar

Here's a very simple ``pre-commit`` script written with `Node.js`_. You can use
any scripting language that you wish as long as it's installed on the system
that runs the plugin.

::

    #!/usr/bin/env node
    process.stdout.write('Always look on the bright side of life');
    process.exit(0);

Running this plugin with Jig will give you output like this:

::

    ▾  myplugin

    ✓  Always look on the bright side of life

    Ran 1 plugin
        Info 1 Warn 0 Stop 0

.. _pluginapi-testing:

Writing tests for your plugins
------------------------------

Before we get too deep into data formats, it's a good time to mention testing.
While it's true that your plugins are probably short and simple, tests can
provide you with a lot of benefit.

Jig provides a framework for writing and running your tests. Let's see it in
action.

Command line
~~~~~~~~~~~~

Tests are ran using Jig's command line tool.

::

    $ jig plugin test -h
    usage: jig plugin test [-h] PLUGIN

    positional arguments:
      plugin         Path to the plugin directory

    optional arguments:
      -h, --help     show this help message and exit
      --verbose, -v  Print the input and output (stdin and stdout)

Create a plugin
~~~~~~~~~~~~~~~

By using :ref:`templates <pluginapi-pre-commit-templates>`, Jig can get you going quickly.

Let's rewrite that Monty Python lyric plugin in...well Python.

We'll call the plugin ``bright-side`` and tell Jig the bundle name is
``pythonlyrics``. (Afterall we'll probably be creating more of these, might as
well bundle them together.)

::

    $ jig plugin create bright-side pythonlyrics
    Created plugin as ./bright-side

The default template is in Python, if we take a look at the :file:`pre-commit`
we can see that it starts with this:

::

    #!/usr/bin/env python

The pre-commit Jig created is too verbose for this example. Remove
everything in there and replace it with this:

::

    #!/usr/bin/env python
    import sys

    sys.stdout.write('Always look on the bright side of life')
    sys.exit(0)

OK, let's run the tests.

::

    $ jig plugin tests bright-side
    Could not find any tests: bright-side/tests.

No tests. We can fix that.

Create test fixtures
~~~~~~~~~~~~~~~~~~~~

If you were writing these plugins without using Jig's testing framework it
would be a pain to test them. You'd either be creating the input data yourself
by hand or using a carefully crafted Git repository.

Jig has a way of making this dead simple. It takes a set of numbered directories
and creates a Git repository for you that your tests can make assertions
against.

.. warning:: This is a strange concept to understand at first. Look at some of
             the tests in Jig's own common plugins if some real examples would help.
             https://github.com/robmadole/jig-plugins/tree/master

To create your fixture we need to start a ``tests`` directory:

::

    $ mkdir bright-side/tests

The next step is to represent the Git repository's *root commit*. Just as the
name implies, this is the very first commit in a repository (it's special
in Git terms because it's the only commit that doesn't have a parent).

Numbering starts at ``01``. We'll create an empty ``README`` file because
we need something of substance for that first commit.

::

    $ mkdir bright-side/tests/01
    $ touch bright-side/tests/01/README

The second commit will be based off the first one, copy the directory to :file:`02`.

::

    $ cp -R bright-side/tests/01 bright-side/tests/02

We need something to change between ``01`` and ``02`` for there to be a commit.

::

    $ echo "The Life of Brian" > bright-side/tests/02/title.txt

With these two directories, Jig has enough information to create an empty
repository with the root commit represented by the **contents** of the ``01``
directory. The next commit, commit #2, will be based on the **contents** of the
``02`` directory.

You don't have to interact with Git at all to make this happen. It's a feature
of Jig's testing framework and it comes for free.

Now that we have a test fixture as a Git repository, run the tests.

::

    $ jig plugin tests bright-side
    Missing expectation file: bright-side/tests/expect.rst.

Still doesn't work. But we're getting closer.

Create the tests
~~~~~~~~~~~~~~~~

Jig's testing file :file:`expect.rst` is a bit unique. Instead of a script that
runs, you **document your plugin to test it**  using `reStructuredText`_.

Create :file:`bright-side/tests/expect.rst` and edit it to read:

::

    Monty Python lyrics
    ===================

    The bright-side plugin simply reminds you to look on the bright side of life.

    .. expectation::
        :from: 01
        :to: 02

reStructuredText is a plaintext markup language. It's similar to Markdown or a
Wiki markup language.

Let's run this test and we can see how this document serves as the description
of the behavior we expect from the plugin.

::

    $ jig plugin test bright-side
    01 – 02 Fail

    Actual
    ················································································

    ▾  bright-side

    ✓  Always look on the bright side of life

    Ran 1 plugin
        Info 1 Warn 0 Stop 0

    Diff
    ················································································

    + ▾  bright-side
    + 
    + ✓  Always look on the bright side of life
    + 
    + Ran 1 plugin
    +     Info 1 Warn 0 Stop 0

Finally we got something.

The key to this is in the ``.. expectations::`` directive you saw in the
:file:`expect.rst` file.

This tells Jig to run the plugin sending it the difference between the first
commit (``01``) and the second commit (``02``) in JSON format.

If we update our :file:`expect.rst` file one we can get a passing test.

.. warning:: Yes, that's Unicode. It's best that you copy and paste instead of
             trying to type this out.

::

    Monty Python lyrics
    ===================

    The bright-side plugin simply reminds you to look on the bright side of life.

    .. expectation::
        :from: 01
        :to: 02

        ▾  bright-side

        ✓  Always look on the bright side of life

        Ran 1 plugin
            Info 1 Warn 0 Stop 0

Run the tests again:

::

    $ jig plugin test bright-side
    01 – 02 Pass

    Pass 1, Fail 0

You've just written automated tests for your new plugin.

While this is a great first step, it was really simple and not very useful.

The next sections will explore the input and output format (in JSON) and how
you can work with this data to make something that actually helps.

Data formats
------------

For plugins to operate in Jig's arena, they have to understand the data coming
in and the data going out. It's JSON both ways.

.. image:: images/input-output.png

The following outlines what you can expect.

Input
~~~~~

The input format is organized by filename. If we turn on verbose output when we
run the tests we can see exactly what Jig is feeding our ``bright-side``
plugin.

::

    $ jig plugin test --verbose bright-side

    01 – 02 Pass

    stdin (sent to the plugin)

        {
          "files": [
            {
              "diff": [
                [
                  1, 
                  "+", 
                  "The Life of Brian"
                ]
              ], 
              "type": "added", 
              "name": "title.txt", 
              "filename": "/Users/ericidle/bright-side/tests/02/title.txt"
            }
          ], 
          "config": {}
        }

    stdout (received from the plugin)

        Always look on the bright side of life

    ················································································
    Pass 1, Fail 0

The JSON object has two members, ``files`` and ``config``.

.. code-block:: javascript
    :emphasize-lines: 2,3

    {
      "files": [ ... ],
      "config": { ... }
    }

Information on files
....................

The ``files`` object contains data about which files changed and what changed
within them.

If we take a look at the first element in the ``files`` array, we can see it contains an
object with ``diff``, ``type``, ``name``, and ``filename`` member.

The ``filename`` value is the **absolute path** of the file.

.. code-block:: javascript
    :emphasize-lines: 5

    {
      "diff": [ ... ],
      "type": "added", 
      "name": "title.txt", 
      "filename": "/Users/ericidle/bright-side/tests/02/title.txt"
    }

The ``name`` value is the name of the filename **relative to the Git
repository**.

.. code-block:: javascript
    :emphasize-lines: 4

    {
      "diff": [ ... ],
      "type": "added", 
      "name": "title.txt", 
      "filename": "/Users/ericidle/bright-side/tests/02/title.txt"
    }

The ``type`` value is the overall action that has occurred to the file. This can
be one of 3 values.

* ``added``
* ``modified``
* ``deleted``

.. code-block:: javascript
    :emphasize-lines: 3

    {
      "diff": [ ... ],
      "type": "added", 
      "name": "title.txt", 
      "filename": "/Users/ericidle/bright-side/tests/02/title.txt"
    }

The ``diff`` is an an array. Each member in the array is also an array and
always contains three values.

#. Line number
#. Type of diff (``+`` is line added, ``-`` is line removed, and " " is
   unchanged)
#. The contents of that line

.. code-block:: javascript
    :emphasize-lines: 3,4,5,6,7

    {
      "diff": [
        [
          1, 
          "+", 
          "The Life of Brian"
        ]
      ], 
      "type": "added", 
      "name": "title.txt", 
      "filename": "/Users/ericidle/bright-side/tests/02/title.txt"
    }

Config data
...........

Along with information about the files, Jig will also pass configuration
settings for a plugin.

It will use the default settings found in the ``[settings]`` section of
:file:`$PLUGIN/config.cfg` and those settings can be overridden by
:file:`$GIT_REPO/.jig/plugins.cfg`.

Our ``bright-side`` plugin doesn't currently have any default settings so let's
add some and see how it affects the JSON input data.

Edit :file:`bright-side/config.cfg`:

.. code-block:: ini
    :emphasize-lines: 6,7

    [plugin]
    bundle = pythonlyrics
    name = bright-side

    [settings]
    sing_also = no
    second_chorus_line = no

Run the tests again:

.. code-block:: bash

    $ jig plugin test --verbose bright-side
    01 – 02 Pass

    stdin (sent to the plugin)

        {
          "files": [
            ...
          ], 
          "config": {
            "second_chorus_line": "no", 
            "sing_also": "no"
          }
        }

    ...

The settings are parsed and made available as *string values only*. If you want
other data types you'll need to convert them yourself.

.. note:: Why string values instead of integers or booleans? The INI format
    doesn't support data types. As opposed to trying to guess the data type and
    take the chance of getting it incorrect, the conversion is left to the
    plugin author.

While testing, Jig provides a directive that allows us to test our plugin based
on different settings.

Edit :file:`bright-side/tests/expect.rst` and add this before the ``..
expectation::`` directive.

.. code-block:: rst
    :emphasize-lines: 3,5,6

    The bright-side plugin simply reminds you to look on the bright side of life.

    .. plugin-settings::

        sing_also = yes
        second_chorus_line = no

    .. expectation::
        :from: 01
        :to: 02

When the test runs this data will be used as 
With this knowledge of the data, we can alter our plugin to provide more detail.

Output
~~~~~~

Line specific messages
~~~~~~~~~~~~~~~~~~~~~~

File specific messages
~~~~~~~~~~~~~~~~~~~~~~

Commit specific messages
~~~~~~~~~~~~~~~~~~~~~~~~

Error handling
--------------

Exit codes
~~~~~~~~~~

Binary files
------------

.. _pluginapi-pre-commit-templates:

Templates for pre-commit scripts
--------------------------------

.. _Node.js: http://nodejs.org/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
