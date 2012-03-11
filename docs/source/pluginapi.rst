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

The :file:`pre-commit` is a shell script, written in any language you choose.

It will recieve JSON data through the ``stdin`` stream. It's expected to write
to ``stdout`` if it has anything to say. A plugin doesn't have to write anything.

The :file:`config.cfg` file contains the plugin name and bundle. Optionally it
can contain settings but they aren't required.

::

    #!/bin/sh
    echo "Always look on the bright side of life"
    exit 0

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
