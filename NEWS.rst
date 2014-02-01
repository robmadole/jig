News
====

*Release 0.1.8 - February 1st, 2014*

* Adds a ``jig report`` command allowing Jig to be ran on any Git revision range.
* Adds a ``jig version`` to show the currently installed version of Jig.

*Release 0.1.7 - December 13th, 2013*

* Fix a missing string to unicode conversion that could cause errors if unicode
  characters were present in the input sent to plugins.

*Release 0.1.6 - April 28th, 2013*

* ``jig config`` command added, allowing plugin configuration settings to be
  managed.

*Release 0.1.5 - April 10th, 2013*

* ``jig runnow`` supports a ``--plugin`` option so that only a specific plugin
  is ran.
* ``jig plugin test`` has a new ``--range`` option to limit the tests ran to a
  specific set instead of the entire suite.

*Release 0.1.4 - March 24th, 2013*

* Jig commands now include more useful messages.
* Periodically checks if installed plugins have updates and prompts to install
  the latest plugins.
* Ignores the .jig directory when running (GitHub Issue #1).

*Release 0.1.3 - February 16th, 2013*

* Makes the indicator between warning messages and stop messages
  easy to discern at a quick glance.
* When Jig runs via the Git pre-commit hook, the output is more pronounced.
* Update the plugin test runner to ignore the summary lines at the bottom of
  the output.

*Release 0.1.2 - February 13th, 2013*

* Support for Python 2.6 when running plugins ``jig plugin test``.

*Release 0.1.1 - February 7th, 2013*

* Upgrade plugins installed from a URL using ``jig plugin update``.
* Python 2.6 support.

*Release 0.1.0 - April 6th, 2012*

* Initial release.
