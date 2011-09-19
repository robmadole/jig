from os.path import isdir

from becareful.exc import GitRepoNotInitialized
from becareful.output import ConsoleView
from becareful.gitutils import repo_bcinitialized


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

        with self.view.out() as out:
            if not repo_bcinitialized(self.gitrepo):
                raise GitRepoNotInitialized('This repository has not been '
                    'initialized. Run becareful init GITREPO to set it up')
