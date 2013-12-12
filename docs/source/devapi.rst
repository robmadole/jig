Hacking on Jig
==============

.. contents::

.. _development-plumbing:

Plumbing of Jig
---------------

How it hooks in
~~~~~~~~~~~~~~~

When you run :ref:`jig init <cli-init>` on a Git repository it does two basic things.

First it creates a :file:`$GIT_REPO/.git/hooks/pre-commit` file and makes it executable.

The file looks something like this:

::

    #!/usr/bin/python
    from sys import path
    from os.path import dirname, join

    # Make sure that we can find the directory that jig is installed
    # ... (various path modifications, don't look behind the curtain)

    from jig.runner import Runner

    # Start up the runner, passing in the repo directory
    jig = Runner()
    jig.fromhook(join(dirname(__file__), '..', '..'))

This is really just a redirection of control to the :py:class:`Runner` object.
It does all the work.

Secondly, it creates a :file:`$GIT_REPO/.jig` directory with a :file:`plugins`
directory and an empty :file:`plugins.cfg` configuration file within it.

As you :ref:`install plugins <cli-plugin-add>` the configuration file will get
modified to includes bits of information about whatever plugin you install.

When you install plugins from a URL, the plugin will be cloned for you
automatically and then placed in the :file:`.jig/plugins` directory.

If we installed the following plugin by running ``jig plugin install http://github.com/myusername/myplugin`` it would be saved in a directory similar to this.
:file:`.jig/plugins/24a8056749e448b182d44690a04ca0b7/myplugin`.

The configuration file :file:`plugins.cfg` will now contain a reference to this
location.

::

  [plugin:mybundle:myplugin]
  path = ./.jig/plugins/24a8056749e448b182d44690a04ca0b7/myplugin
  crank_widget = yes

It also contains the **default settings** for this plugin as defined by the
author. You can change these settings to affect the way the plugin behaves.

How it runs
~~~~~~~~~~~

Git automatically runs Jig when ``git commit`` is ran. It happens before your
staged files become an object in the Git database (before your commit is
written).

The neat part of this is that **if Jig returns an exit code of 0** the commit
will occur. But **if Jig returns a non-zero exit code like 1**, Git will abort the
commit.

Jig communicates with plugins using the `JSON`_ data format. Both the input and
the output are JSON. This is convenient because almost all scripting languages
that will likey be used to write Jig plugins can easily deal with JSON data.

A plugin has the ability to pass messages back to Jig that will be formatted
and displayed in the terminal.

.. image:: images/integration.png

.. _JSON: http://www.json.org/

Developing Jig
--------------

Running the tests, building the documentation, and cutting releases to PyPi are
all done through the Jig development environment.

The environment is managed by Vagrant_ and uses VMware as the virtualization
layer.

Install Vagrant, VWmare Fusion/Workstation, and the Vagrant `VMware plugin`_ that
allows Vagrant to support VMware and then proceed.

Clone the Jig repository:

::

    $ git clone https://github.com/robmadole/jig.git

Bring up the environment:

::

    $ cd jig
    $ vagrant up --provider vmware_fusion

After the environment is up, login:

::

    $ vagrant ssh

You should see some instructions on where to proceed as part of the Linux
message-of-the-day.

.. _Vagrant: http://vagrantup.com
.. _VMware plugin: http://www.vagrantup.com/vmware
