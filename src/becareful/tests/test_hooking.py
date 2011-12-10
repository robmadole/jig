from os import rmdir
from os.path import join, realpath
from tempfile import mkdtemp

from becareful.tests.testcase import BeCarefulTestCase
from becareful.exc import NotGitRepo, PreCommitExists
from becareful.gitutils import hook


class TestAddingHook(BeCarefulTestCase):

    """
    Can we properly hook a Git repository

    """
    def setUp(self):
        # Where will our pre-commit file be?
        self.pc_filename = realpath(join(self.gitrepodir, '.git', 'hooks',
            'pre-commit'))

    def test_not_git_directory(self):
        """
        The directory given is not a repo.
        """
        badrepo = mkdtemp()

        try:
            with self.assertRaises(NotGitRepo) as c:
                hook(badrepo)
        finally:
            rmdir(badrepo)

    def test_will_stop_if_pre_commit_exists(self):
        """
        Stop if .git/hooks/pre-commit exists
        """
        # Let's create a pre-commit hook, which we would use
        with open(self.pc_filename, 'w') as fh:
            fh.write('#!/bin/sh')

        with self.assertRaises(PreCommitExists) as c:
            hook(self.gitrepodir)

    def test_successfully_hooks(self):
        """
        Creates the pre-commit hook.
        """
        pc_filename = hook(self.gitrepodir)

        self.assertEqual(self.pc_filename,
            pc_filename)

    def test_hook_runs(self):
        """
        New hook will run.
        """
        pc_filename = hook(self.gitrepodir)

        retcode, output = self.runcmd(pc_filename)

        self.assertEqual(1, retcode)
        self.assertEqual('This repository has not been initialized. Run '
            'becareful init GITREPO to set it up\n', output)
