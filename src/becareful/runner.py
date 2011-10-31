from os.path import isdir

from becareful.exc import GitRepoNotInitialized, NoPluginsInstalled
from becareful.output import ConsoleView
from becareful.gitutils import repo_bcinitialized
from becareful.plugins import get_bcconfig, PluginManager


class Runner(object):

    """
    Runs BeCareful in a Git repo.

    """
    def __init__(self):
        self.view = ConsoleView()

    def fromhook(self, gitrepo):
        """
        Main entry point for running, typically called from pre-commit hook.
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

        # Get the diff on the repository, let see if we have any work to do
        import pdb; pdb.set_trace();
