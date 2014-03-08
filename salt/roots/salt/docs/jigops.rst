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

    vagrant@raring64:/vagrant$ /envs/python2.6/bin/python script/test

Python 2.7:

::

    vagrant@raring64:/vagrant$ /envs/python2.7/bin/python script/test

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

Rebuilding the base box
-----------------------

Inside the ``packer`` directory are Packer.io files to build the base box that
Jig uses for Vagrant.

Install packer - ``brew install packer`` will do it - and then run the following:

**Note** you have to do this from the host operating system, not from within Vagrant.

::

    packer build jig-development-environment.json

This will take a while. After the process is complete you should find a Vagrant
.box file inside of the ``packer/vmware`` directory.

Remove any existing box that has already been downloaded from a previous `vagrant up`.

::

    vagrant box remove jig-development-vmware

Uploading the base box to AWS
-----------------------------

A convenient location to store a base box is within Amazon's S3.

Create a bucket in ``us-east-1`` in the S3 service called "jig-base-boxes" and
enable static content serving.

To upload the box, install the ``awscli`` official client:

::

    pip install awscli

Configure a user in the IAM service for Jig and use the access key and secret
to configure the command-line client.

::

    aws configure --profile jig

Upload the box to S3.

::

    aws s3 --profile jig \
      --region us-east-1 \
      cp vagrant/jig-development-vmware.box s3://jig-base-boxes/jig-development-vmware.box

Make it public.

::

    aws s3api --profile jig \
      --region us-east-1 \
      put-object-acl \
      --grant-read 'uri=http://acs.amazonaws.com/groups/global/AllUsers' \
      --key jig-development-vmware.box
      --bucket jig-base-boxes \
