import json
from collections import OrderedDict

from git import Repo

from becareful.exc import GitRepoNotInitialized, NoPluginsInstalled
from becareful.gitutils import repo_bcinitialized
from becareful.diffconvert import GitDiffIndex
from becareful.plugins import get_bcconfig, PluginManager
from becareful.commands import get_command, list_commands
from becareful.output import ConsoleView


class Runner(object):

    """
    Runs BeCareful in a Git repo.

    """
    def __init__(self, view=None):
        self.view = view or ConsoleView()

    def fromhook(self, gitrepo):
        """
        Main entry point for running, typically called from pre-commit hook.

        Where ``gitrepo`` is the file path to the Git repository.
        """
        results = self.results(gitrepo)

        self.view.print_results(results)

    def fromconsole(self, argv):
        """
        Console entry point for the becareful script.

        Where ``argv`` is ``sys.argv``.
        """
        # Quick copy
        argv = argv[:]
        # Our script is the first element
        argv.pop(0)

        try:
            # Next argument is the command
            command = get_command(argv.pop(0))
            command(argv)
        except (ImportError, IndexError):
            # If it's empty
            self.view.print_help(list_commands())

    def results(self, gitrepo):
        """
        Run BeCareful in the repository and return results.

        Results will be a dictionary where the keys will be individual plugins
        and the value the result of calling their ``pre_commit()`` methods.
        """
        self.gitrepo = gitrepo

        # Is this repository initialized to use BeCareful on?
        with self.view.out() as out:
            if not repo_bcinitialized(self.gitrepo):
                raise GitRepoNotInitialized('This repository has not been '
                    'initialized. Run becareful init GITREPO to set it up')

        pm = PluginManager(get_bcconfig(self.gitrepo))

        # Check to make sure we have some plugins to run
        with self.view.out() as out:
            if len(pm.plugins) == 0:
                raise NoPluginsInstalled('There are no plugins installed, '
                    'use becareful install to add some')

            self.repo = Repo(gitrepo)

            try:
                diff = self.repo.head.commit.diff()
            except ValueError:
                # No diff on head, no commits have been written yet
                out.append('This repository is empty, BeCareful needs at least '
                    '1 commit to continue')
                # Let execution continue so they *can* commit that first
                # changeset.
                return

            if len(diff) == 0:
                # There is nothing changed in this repository, no need for
                # becareful to run
                out.append('No staged changes in the repository, skipping '
                    'BeCareful')
                return

        # Our git diff index is an object that makes working with the diff much
        # easier in the context of our plugins.
        gdi = GitDiffIndex(self.gitrepo, diff)

        # Go through the plugins and gather up the results
        results = OrderedDict()
        for plugin in pm.plugins:
            retcode, stdout, stderr = plugin.pre_commit(gdi)

            try:
                # Is it JSON data?
                data = json.loads(stdout)
            except ValueError:
                # Not JSON
                data = stdout

            results[plugin] = (retcode, data, stderr)

        return results


