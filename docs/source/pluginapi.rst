Plugin API
==========

Writing plugins for Jig is simple. The plugin is sent data over stdin and it
writes it's output to stdout. For both in and out, it's dealing with JSON.

.. _pluginapi-anatomy:

The anatomy of a plugin
-----------------------

The most basic plugin has just two files:

* pre-commit
* config.cfg

The :file:`pre-commit` is your script and :file:`config.cfg` contains info about your plugin.

It will recieve JSON data through the ``stdin`` stream. It's expected to write
to ``stdout`` if it has anything to say. A plugin doesn't have to write anything.

The :file:`config.cfg` file contains the plugin name and bundle. Optionally it
can contain settings but they aren't required.

Here's an example:

::

    [plugin]
    bundle = mybundle
    name = myplugin

    [settings]

If you plan on making more than one plugin and you'd like to keep them grouped
together, keep the ``bundle`` identifier the same.

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

.. _pluginapi-testing:

Testing
-------

.. _pluginapi-pre-commit-templates:

Templates for pre-commit scripts
--------------------------------

.. _Node.js: http://nodejs.org/
