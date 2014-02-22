from os import rmdir
from os import access, X_OK
from os.path import join, realpath, isdir, isfile, expanduser
from tempfile import mkdtemp

import git
from mock import patch, Mock

from jig.tests.testcase import JigTestCase, result_with_hint
from jig.commands.hints import GIT_REPO_NOT_INITIALIZED
from jig.exc import (
    NotGitRepo, PreCommitExists, GitTemplatesMissing,
    JigUserDirectoryError, GitHomeTemplatesExists, InitTemplateDirAlreadySet,
    GitConfigError)
from jig.gitutils.hooking import (
    hook, _git_templates, create_auto_init_templates, set_templates_directory)


class TestHook(JigTestCase):

    """
    Can we properly hook a Git repository

    """
    def setUp(self):
        super(TestHook, self).setUp()

        # Where will our pre-commit file be?
        self.pc_filename = realpath(
            join(self.gitrepodir, '.git', 'hooks', 'pre-commit')
        )

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

        self.assertEqual(self.pc_filename, pc_filename)

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


class TestGitTemplates(JigTestCase):

    """
    Function that finds the shared Git templates.

    """
    def test_will_find_one(self):
        """
        Can find a shared Git directory.
        """
        self.assertIsNotNone(_git_templates())

    def test_returns_none_if_not_found(self):
        """
        Returns None if it cannnot find any templates.
        """
        with patch('jig.gitutils.hooking.isdir') as isdir:
            isdir.return_value = False

            self.assertIsNone(_git_templates())


class TestCreateAutoInitTemplates(JigTestCase):

    """
    An auto-init templates directory can be created.

    """
    def setUp(self):
        super(TestCreateAutoInitTemplates, self).setUp()

        self.user_home_directory = mkdtemp()
        self.git_templates = \
            'jig.gitutils.hooking._git_templates'

    def test_raises_exception_permission_denied(self):
        """
        Raise if the .jig directory can't be created due to permissions.
        """
        with patch('jig.gitutils.hooking.makedirs') as makedirs:
            makedirs.side_effect = OSError(13, 'Permission denied')

            with self.assertRaises(JigUserDirectoryError) as ec:
                create_auto_init_templates(self.user_home_directory)

        self.assertEqual(
            u'Cannot create {0}/.jig Jig user directory'.format(
                self.user_home_directory),
            unicode(ec.exception)
        )

    def test_raises_exception_other_os_error(self):
        """
        Raise if some other kind of OSError is found.
        """
        with patch('jig.gitutils.hooking.makedirs') as makedirs:
            makedirs.side_effect = OSError(99, 'Flooglehorn is blocked')

            with self.assertRaises(JigUserDirectoryError) as ec:
                create_auto_init_templates(self.user_home_directory)

        self.assertEqual(
            u'[Errno 99] Flooglehorn is blocked',
            unicode(ec.exception)
        )

    def test_continues_if_jig_user_directory_created(self):
        """
        An existing ~/.jig directory doesn't cause failure.
        """
        with patch('jig.gitutils.hooking.makedirs') as makedirs:
            makedirs.side_effect = OSError(17, 'Directory exists')

        self.assertEqual(
            '{0}/.jig/git/templates'.format(self.user_home_directory),
            create_auto_init_templates(self.user_home_directory)
        )

    def test_raises_exception_if_no_templates(self):
        """
        If no Git templates can be found raise an exception.
        """
        with patch(self.git_templates) as gtsl:
            gtsl.return_value = None

            with self.assertRaises(GitTemplatesMissing):
                create_auto_init_templates(self.user_home_directory)

    def test_creates_the_templates_directory(self):
        """
        The templates are copied from the Git shared directory.
        """
        home_templates_directory = create_auto_init_templates(
            self.user_home_directory
        )

        self.assertTrue(isdir(home_templates_directory))

    def test_already_created(self):
        """
        Will raise an exception when it's already created the templates.
        """
        create_auto_init_templates(self.user_home_directory)

        with self.assertRaises(GitHomeTemplatesExists):
            create_auto_init_templates(self.user_home_directory)

    def test_creates_pre_commit_hook(self):
        """
        Creates the pre-commit hook for auto-initialization.
        """
        templates_directory = create_auto_init_templates(
            self.user_home_directory
        )

        self.assertTrue(
            isfile(join(templates_directory, 'hooks', 'pre-commit'))
        )

    def test_pre_commit_hook_is_executable(self):
        """
        Once created it can be executed.
        """
        templates_directory = create_auto_init_templates(
            self.user_home_directory
        )

        self.assertTrue(
            access(join(templates_directory, 'hooks', 'pre-commit'), X_OK)
        )


class TestSetTemplatesDirectory(JigTestCase):

    """
    The Git config can be changed to use the Jig templates directory.

    """
    def setUp(self):
        super(TestSetTemplatesDirectory, self).setUp()

        self.templates_directory = create_auto_init_templates(mkdtemp())

        self._clear_gitconfig()

    @classmethod
    def tearDownClass(cls):
        cls._clear_gitconfig()

    @classmethod
    def _clear_gitconfig(self):
        # Reset the global Git config
        with open(expanduser('~/.gitconfig'), 'w') as fh:
            fh.write('')

    def test_error_reading_git_config(self):
        """
        Raises an exception if there are problems reading the Git config.
        """
        with patch('jig.gitutils.hooking.git.cmd') as mock_cmd:
            mock_command = Mock()
            mock_command.config.side_effect = git.exc.GitCommandError(
                'git config', 1, 'error'
            )

            mock_cmd.Git.return_value = mock_command

            with self.assertRaises(GitConfigError) as gce:
                set_templates_directory(self.templates_directory)

        self.assertEqual(
            u'Problem when running git config: error',
            unicode(gce.exception)
        )

    def test_init_templatedir_already_set(self):
        """
        Will raise an exception if the config already has init.templatedir set.
        """
        git.cmd.Git().config(
            '--global', '--add', 'init.templatedir', '/tmp/templates'
        )

        with self.assertRaises(InitTemplateDirAlreadySet):
            set_templates_directory(self.templates_directory)

    def test_sets_templatedir(self):
        """
        Will set the templatedir.
        """
        set_templates_directory(self.templates_directory)

        config = git.cmd.Git().config('--global', '--list')

        self.assertIn(
            'init.templatedir',
            config
        )

        self.assertIn(
            self.templates_directory,
            config
        )

    def test_raises_exception_if_cannot_write(self):
        """
        Raises an exception if it can't write to the Git config.
        """
        side_effects = [
            '',
            git.exc.GitCommandError('', 1, 'error')
        ]

        def config(*args, **kwargs):
            se = side_effects.pop(0)
            if isinstance(se, Exception):
                raise se
            else:
                return se

        with patch('jig.gitutils.hooking.git.cmd') as mock_cmd:
            mock_command = Mock()
            mock_command.config.side_effect = config
            mock_cmd.Git.return_value = mock_command

            with self.assertRaises(GitConfigError):
                set_templates_directory(self.templates_directory)
