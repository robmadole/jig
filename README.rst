* This is currently a work in progress, this documentation is fake; I haven't
  written the code that makes any of this work.

Jig
===

Check your code before you commit.

BeCareful is a framework for finding code smells, checking code style, or performing
other lint-like operations before you create a changeset.

Why
---

We all make mistakes. How many times have you left a ``debugger;`` line in your
JavaScript and pushed the changeset to a remote repository?

BeCareful helps you avoid commit messages like "Ooops, forgot to remove a
pdb.set_trace()". It won't prevent you from making mistakes but it can help you
find them before it's too late.

How does it work
----------------

With Git hooks and a bit of glue code to some existing tools you've probably
already used. You can use existing adapters to tools like ``jslint`` or ``pep8``
or you can write your own.

Getting started
---------------

Install the Git hook in an existing repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need an existing Git repository for this to work. If you want to try this
out with an empty repository you can do this.

::

    mkdir projectx
    git init projectx

Now install BeCareful::

    pip install becareful

Change directories into your repo and initialize it::

    becareful init .

So what just happened? A small Git hook was created that gives BeCareful access
to the changes that you make when you attempt to create a commit. If you're
curious, it's in ``.git/hooks/pre-commit``.

TODOC

Install some scripts
~~~~~~~~~~~~~~~~~~~~

BeCareful isn't useful by itself. It's really designed just to glue together
other scripts in a unified interface. You need to install some scripts before it
will do anything worthwhile.

From within your repository::

    becareful add --git https://github.com/robmadole/becareful-bundle.git

You can start with some simple scripts that are bundled along side of BeCareful.
It's easy to write your own.

Writing your own scripts
------------------------

TODOC
