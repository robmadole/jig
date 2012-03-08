Hacking on Jig and internal API
===============================

Tests and coverage
------------------

Jig uses `Nose`_ to run tests and `coverage.py`_ to perform code coverage
analysis.

You need to have a cloned copy of Jig to run either one. You can start with a
read-only copy:

::

    $ git clone git://github.com/robmadole/jig.git

Or `fork the repository`_ on GitHub to make your own changes. The
:doc:`Jig License <license>` is friendly.

.. _development-buildout:

Jig also uses zc.buildout, which means you need to run a couple of commands to
download dependencies and create the scripts needed for development.

::

    $ python boostrap.py && ./bin/buildout

To run the tests:

::

    $ ./bin/jig-tests

To run test coverage:

::

    $ ./bin/jig-coverage

.. _Nose: http://readthedocs.org/docs/nose/en/latest/
.. _coverage.py: http://nedbatchelder.com/code/coverage/
.. _fork the repository: https://github.com/robmadole/jig/fork_select

Making the documentation
------------------------

This documentation is made with Sphinx_. To build the docs make sure you've ran
the :ref:`buildout <development-buildout>` first.


Build the HTML version:

::

    $ cd docs
    $ make html

The builds will be placed in :file:`build`.

.. _Sphinx: http://sphinx.pocoo.org/

.. _development-plumbing:

Plumbing of Jig
---------------

Jig is a file-based tool. It creates directories and files to facilitate its work.



Objects used internally by Jig to interface with Git.

jig.diffconvert
---------------

.. automodule:: jig.diffconvert
   :members:

jig.conf
--------

.. automodule:: jig.conf
   :members:

jig.exc
-------

.. automodule:: jig.exc
   :members:

jig.gitutils
------------

.. automodule:: jig.gitutils
   :members:

jig.output
----------

.. automodule:: jig.output
   :members:

jig.plugins
-----------

.. automodule:: jig.plugins
   :members:

jig.runner
----------

.. automodule:: jig.runner
   :members:

jig.tools
---------

.. automodule:: jig.tools
   :members:
