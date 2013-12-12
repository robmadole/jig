Jig operations environment
==========================

Jig is Open Source and any contributions are welcome.

Fork the repository on GitHub to make your own changes. The
Jig License is friendly.

Using this environment
----------------------

This environment uses Vagrant and Salt. If anything goes wrong you can
try these things.

Re-provision the environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If something is not working as expected, the environment may be
something other than highstate (current). You can trigger a provisioning
of the environment two ways.

From your host machine (Mac or Unix-like OS):

::

    $ vagrant provision

From within the Vagrant environment:

::

    vagrant@raring64:~$ sudo salt-call state.highstate

If all else fails you can destroy the Vagrant environment and start
over:

::

    $ vagrant destroy
    $ vagrant up --provider vmware_fusion

Run tests
---------

Python 2.6:

::

    vagrant@raring64:~$ /envs/python2.6/bin/python script/test

Python 2.7:

::

    vagrant@raring64:~$ /envs/python2.7/bin/python script/test

Coverage report
---------------

This will run the tests and user coverage.py to examine code coverage.

::

    vagrant@raring64:~$ /envs/python2.6/bin/python script/coverage

Substitute ``python2.6`` with the Python version you'd like to use just
like you did when running tests only.

.. _coverage.py: http://nedbatchelder.com/code/coverage/
.. _Fork the repository: https://github.com/robmadole/jig/fork_select

Cutting a release
-----------------

Releases are cut from the develop branch, start there.

#. Create the release branch (see gitflow_, Jig uses this branching model)
#. Edit ``NEWS.rst``
#. Edit ``src/jig/__init__.py``
#. Edit ``docs/source/conf.py`` version number
#. Commit, checkout ``master`` and ``git merge --no-ff`` the release branch
#. Tag the release ``git tag``
#. ``git push --tags origin master``
#. Release to PyPi ``python setup.py sdist register upload``
#. Checkout ``develop`` and merge ``master``
#. Zip the docs up and upload

.. _gitflow: http://nvie.com/posts/a-successful-git-branching-model/
