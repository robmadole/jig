from os import rmdir
from os.path import join, realpath
from tempfile import mkdtemp

from jig.tests.testcase import JigTestCase, result_with_hint
from jig.commands.hints import GIT_REPO_NOT_INITIALIZED
from jig.exc import NotGitRepo, PreCommitExists
from jig.gitutils import hook


class TestAddingHook(JigTestCase):

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
            with self.assertRaises(NotGitRepo):
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

        with self.assertRaises(PreCommitExists):
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
        self.assertResults(
            result_with_hint(
                u'This repository has not been initialized.',
                GIT_REPO_NOT_INITIALIZED),
            output)
