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

The :file:`config.cfg` file contains the plugin name and bundle. Optionally it
can contain settings but they aren't required.

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

The output of this plugin would be:

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

The first benefit with Jig is that it provides a framework for writing and
running your tests. Let's see it in action.

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

The example is more thorough than we need right now. Remove everything in there
and replace it with this:

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

Jig takes a set of numbered directories and creates a Git repository for you
that your tests can make assertions against.

.. warning:: This is a strange concept to understand at first. Look at some of
             the tests in Jig's own common plugins if some real examples would help.
             https://github.com/robmadole/jig-plugins/tree/master

To create your fixture we need to start a ``tests`` directory:

::

    $ mkdir bright-side/tests

The next step is to represent the Git repository's *root commit*. Just as the
name implies, this is the very first commit in a repository (it's special
because it's the only commit that doesn't have a parent).

Our number start at ``01``. We'll also create an empty ``README`` file because
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

Run the tests.

::

    $ jig plugin tests bright-side
    Missing expectation file: bright-side/tests/expect.rst.

Still doesn't work. We can fix that.

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

This is fairly straight-forward and if you're accustomed to using
reStructuredText you will feel right at home. Let's run this test and things
will start to make more sense.

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

The key to this is in the ``.. expectations::`` directive you saw in the :file:`expect.rst` file.

This tells Jig to run the plugin sending it the difference between the first
commit (``01``) and the second commit (``02``) in JSON format.

If we update our :file:`expect.rst` file one more time we should get better results.

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

Incoming
--------

Outgoing
--------

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
