How to write plugins
====================

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

.. code-block:: ini

    [plugin]
    bundle = mybundle
    name = myplugin

    [settings]

.. note:: If you plan on making more than one plugin and you'd like to keep
          them grouped together, keep the ``bundle`` identifier the same.

If you want to add settings to your plugin which can be read by your ``pre-commit`` script, you can do that like this:

.. code-block:: ini

    [plugin]
    bundle = mybundle
    name = myplugin

    [settings]
    verbose = no
    foo = bar

Here's a very simple ``pre-commit`` script written with `Node.js`_. You can use
any scripting language that you wish as long as it's installed on the system
that runs the plugin.

.. code-block:: javascript

    #!/usr/bin/env node
    process.stdout.write('Always look on the bright side of life');
    process.exit(0);

Running this plugin with Jig will give you output like this:

.. code-block:: console

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

.. code-block:: console

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

.. code-block:: console

    $ jig plugin create bright-side pythonlyrics
    Created plugin as ./bright-side

The default template is in Python, if we take a look at the :file:`pre-commit`
we can see that it starts with this:

.. code-block:: python

    #!/usr/bin/env python

The pre-commit Jig created is too verbose for this example. Remove
everything in there and replace it with this:

.. code-block:: python

    #!/usr/bin/env python
    import sys

    sys.stdout.write('Always look on the bright side of life')
    sys.exit(0)

OK, let's run the tests.

.. code-block:: console

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

.. code-block:: console

    $ mkdir bright-side/tests

The next step is to represent the Git repository's *root commit*. Just as the
name implies, this is the very first commit in a repository (it's special
in Git terms because it's the only commit that doesn't have a parent).

Numbering starts at ``01``. We'll create an empty ``README`` file because
we need something of substance for that first commit.

.. code-block:: console

    $ mkdir bright-side/tests/01
    $ touch bright-side/tests/01/README

The second commit will be based off the first one, copy the directory to :file:`02`.

.. code-block:: console

    $ cp -R bright-side/tests/01 bright-side/tests/02

We need something to change between ``01`` and ``02`` for there to be a commit.

.. code-block:: console

    $ echo "The Life of Brian" > bright-side/tests/02/title.txt

With these two directories, Jig has enough information to create an empty
repository with the root commit represented by the **contents** of the ``01``
directory. The next commit, commit #2, will be based on the **contents** of the
``02`` directory.

You don't have to interact with Git at all to make this happen. It's a feature
of Jig's testing framework and it comes for free.

Now that we have a test fixture as a Git repository, run the tests.

.. code-block:: console

    $ jig plugin tests bright-side
    Missing expectation file: bright-side/tests/expect.rst.

Still doesn't work. But we're getting closer.

Create the tests
~~~~~~~~~~~~~~~~

Jig's testing file :file:`expect.rst` is a bit unique. Instead of a script that
runs, you **document your plugin to test it**  using `reStructuredText`_.

Create :file:`bright-side/tests/expect.rst` and edit it to read:

.. code-block:: rst

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

.. code-block:: console

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

.. code-block:: rst

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

.. code-block:: console

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

.. _pluginapi-input:

Input
~~~~~

The input format is organized by filename. If we turn on verbose output when we
run the tests we can see exactly what Jig is feeding our ``bright-side``
plugin.

.. code-block:: console
    :emphasize-lines: 1

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

.. code-block:: console

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

Edit :file:`bright-side/tests/expect.rst` and add another section and test to
our expectations.

.. code-block:: rst
    :emphasize-lines: 20

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

    Sing to me
    ~~~~~~~~~~

    It will sing to you. Change the ``sing_also`` to ``yes`` to get some additional
    output.

    .. plugin-settings::

        sing_also = yes
        second_chorus_line = no

    .. expectation::
        :from: 01
        :to: 02

        ▾  bright-side

        ✓  Always look on the bright side of life

        Ran 1 plugin
            Info 1 Warn 0 Stop 0

Our :file:`pre-commit` script hasn't been altered to use this new setting so
running the test again will show that this passes.

.. code-block:: console

    $ jig plugin test bright-side
    01 – 02 Pass

    01 – 02 Pass

    Pass 2, Fail 0

Change the :file:``bright-side/pre-commit`` script to this:

.. code-block:: python
    :emphasize-lines: 4,6,8,9

    #!/usr/bin/env python
    # coding=utf-8
    import sys
    import json

    data = json.loads(sys.stdin.read())

    if data['config']['sing_also'] == 'yes':
        message = '♫ Always look on the bright side of life ♫'
    else:
        message = 'Always look on the bright side of life'

    sys.stdout.write(message)
    sys.exit(0)

The next test result will show a failure because of our altered setting.

.. code-block:: console

    01 – 02 Pass

    01 – 02 Fail

    Actual
    ················································································

    ▾  bright-side

    ✓  ♫ Always look on the bright side of life ♫

    Ran 1 plugin
        Info 1 Warn 0 Stop 0

    Diff
    ················································································

      ▾  bright-side

    - ✓  Always look on the bright side of life
    + ✓  ♫ Always look on the bright side of life ♫

      Ran 1 plugin
          Info 1 Warn 0 Stop 0

    Pass 1, Fail 1

Change the expectation to look for our singing version of the chorus.

.. code-block:: rst

    .. plugin-settings::

        sing_also = yes
        second_chorus_line = no

    .. expectation::
        :from: 01
        :to: 02

        ▾  bright-side

        ✓  ♫ Always look on the bright side of life ♫

        Ran 1 plugin
            Info 1 Warn 0 Stop 0

With that change it should bring our tests back to a passing state.

.. code-block:: console

    $ jig plugin test bright-side
    01 – 02 Pass

    01 – 02 Pass

    Pass 2, Fail 0

.. warning:: The ``.. plugin-settings::`` directive is sticky to a section. It
    doesn't apply just once for the next ``.. expectation::`` directive but will
    continue to apply until a section change. Sections in our example are
    separated by ``~~~~~~~~~~~~~~~``.

Output
~~~~~~

Now that we are familiar with the input format, it's time to improve our
:file:`pre-commit` script and give it a little more whizbang by specifying
output.

Info, warnings, and stops
.........................

Jig supports three basic types of messages.

* **info** (you can shorten this to "i")
* **warn** (you can shorten this to "w")
* **stop** (you can shorten this to "s")

**The default type is ``info``**

They are displayed to the user with differently and tallied individually at the
end of Jig's execution.

.. code-block:: console

    ▾  Plugin 1

    ✓  info

    ⚠  warn

    ✕  stop

.. _pluginapi-simple-messages:

Simple messages
...............

A simple message is not specific to a file or a line in a file. It's used to
communicate something to the user that is more general.

Examples:

.. code-block:: javascript

    [
        'Your commit looks really good, excellent job'
    ]

More than one message:


.. code-block:: javascript

    [
        'Your commit looks really good, excellent job',
        'Give yourself a pat on the back'
    ]

This will produce output similar to this:

.. code-block:: console

    ▾  My-Plugin

    ✓  Your commit looks really good, excellent job

    ✓  Give yourself a pat on the back

    Ran 1 plugin
        Info 1 Warn 0 Stop 0

The default message type is ``info`` but you can change it by providing an array
of ``[TYPE, MESSAGE]``.

.. code-block:: javascript

    [
        ['w', 'Your commit looks a little janky'],
        ['s', 'On second thought, this is a horrible commit']
    ]

The output will look like this:

.. code-block:: console

    ▾  My-Plugin

    ⚠  Your commit looks a little janky

    ✕  On second thought, this is a horrible commit

    Ran 1 plugin
        Info 0 Warn 1 Stop 1

File messages
.............

File messages are specific to files but not to a particular line.

Examples:

.. code-block:: javascript

    {
        'myMainFile.javascript': [
            'The extension should probably just be .js',
            'You should not camelCase your JavaScript filenames'
        ]
    }

The output will include the filename:

.. code-block:: console

    ▾  My-Plugin

    ✓  myMainFile.javascript
        The extension should probably just be .js

    ✓  myMainFile.javascript
        You should not camelCase your JavaScript filenames

    Ran 1 plugin
        Info 2 Warn 0 Stop 0

You can specify the type of message:

.. code-block:: javascript

    {
        'myMainFile.javascript': [
            ['i', 'The extension should probably just be .js'],
            ['w', 'You should not camelCase your JavaScript filenames'],
            ['s', 'Really? Putting "File" in the name of your file?']
        ]
    }

The output is:

.. code-block:: console

    ▾  My-Plugin

    ✓  myMainFile.javascript
        The extension should probably just be .js

    ⚠  myMainFile.javascript
        You should not camelCase your JavaScript filenames

    ✕  myMainFile.javascript
        Really? Putting "File" in the name of your file?

    Ran 1 plugin
        Info 1 Warn 1 Stop 1

Line messages
.............

These are very similar to file messages but include the line number.

Examples:

.. code-block:: javascript

    {
        'utils.sh': [
            [1, 's', 'You don't have a hashbang (#!) as the first line'],
        ]
    }

This will include the line number in the output:

.. code-block:: console

    ▾  My-Plugin

    ✕  line 1: utils.sh
        You don't have a hashbang (#!) as the first line

    Ran 1 plugin
        Info 0 Warn 0 Stop 1

Multiple messages for the file can be specified:

.. code-block:: javascript

    {
        'utils.sh': [
            [1, 's', 'You don't have a hashbang (#!) as the first line'],
            [5, 'i', 'This is a bash style if statement and will fail with sh'],
            [500, 'w', "Getting a bit long is it not? You could use Python instead...']
        ]
    }

The output:

.. code-block:: console

    ▾  My-Plugin

    ✕  line 1: utils.sh
        You don't have a hashbang (#!) as the first line

    ✓  line 1: utils.sh
        This is a bash style if statement and will fail with sh

    ⚠  line 1: utils.sh
        Getting a bit long is it not? You could use Python instead...

    Ran 1 plugin
        Info 1 Warn 1 Stop 1

Non-JSON output
...............

In our examples for the :ref:`input <pluginapi-input>` formatting, our
:file:`pre-commit` script simply printed the messages directly to standard out.
They were not in JSON format. Jig is forgiving of this and will not reject
messages that come in this way.

The output will be treated as :ref:`simple messages <pluginapi-simple-messages>`
but you'll have to format newlines yourself.

The following examples are equivalent:

.. code-block:: python

    # As a string with a newline
    sys.stdout.write('Simple message one')
    sys.exit(0)

.. code-block:: python

    # As JSON
    sys.stdout.write(json.dumps(
        ['Simple message one']))
    sys.exit(0)

The output for both of these would be

.. code-block:: console

    ▾  My-Plugin

    ✓  Simple message one

    Ran 1 plugin
        Info 1 Warn 0 Stop 0

Error handling
--------------

Jig pays attention to both the standard out and the standard error streams.

If your plugins exits with an exit code of **1**, any data that is written to
``stderr`` will be displayed to the user.

.. code-block:: console

    ▾  jslint

    ✕  You need the jslint command line tool installed before running this plugin

    Ran 1 plugin
        Info 0 Warn 0 Stop 0
        (1 plugin reported errors)

When you are writing tests for you plugin, these are formatted in a friendly way
to aid in debugging.

.. code-block:: console

    Actual
    ················································································

    Exit code: 1

    Std out:
    (none)

    Std err:
    You need the jslint command line tool installed before running this plugin


Exit codes
~~~~~~~~~~

Plugins should always exit with **0** or **1**.

Exiting with 0
..............

An exit code of **0** means *the plugin functioned normally*. Even if it
generated warnings or stop messages.

Exiting with 1
..............

If your plugin fails to function as expected, it should exit witth **1**. This
indicates to Jig that a problem exists and the output, if any, from the plugin
is not a normal collection of messages that Jig will understand.

A common reason for exiting with **1** would be a missing dependency.

.. code-block:: python

    import sys
    from subprocess import call, PIPE

    # which exits with 1 if it can't find the command
    if call(['which', 'jslint'], stdout=PIPE) == 1:
        # Write to stderr, not stdout
        sys.stderr.write('Could not find JSlint, do you need to install it?')
        sys.exit(1)

Binary files
------------

Jig does not currently support binary files. It doesn't ignore them, but you
will not get any data back in the ``diff`` section.

For example, if an image was added you'll see something like this:

.. code-block:: javascript

    {
      "files": [
        {
          "diff": [], 
          "type": "added", 
          "name": "some-image.png", 
          "filename": "/Users/ericidle/bright-side/tests/02/some-image.png"
        }, 
      ]
    }

Symlinks
--------

Git supports symlinks but Jig will ignore them. This may change in the future,
but since they cannot be treated the same as normal files a lot of plugin
authors would not perform the additional error handling needed.

If you have a valid case for needing to know about symlinks, submit a `feature
request`_.

.. _pluginapi-pre-commit-templates:

Templates for pre-commit scripts
--------------------------------

Jig currently comes with one template.

When you run the following command:

.. code-block:: console

    $ jig plugin create my-plugin my-bundle

The templates can be found at:

https://github.com/robmadole/jig/tree/master/src/jig/data/pre-commits

At the moment the only template is Python. More are planned in the future.

.. _Node.js: http://nodejs.org/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _feature request: http://github.com/robmadole/jig/issues/new
