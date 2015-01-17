# coding=utf-8
from mock import patch, MagicMock

from jig.tests.testcase import CommandTestCase, result_with_hint
from jig.commands import sticky
from jig.gitutils.commands import git
from jig.exc import (
    ForcedExit, JigUserDirectoryError, GitConfigError,
    InitTemplateDirAlreadySet, GitTemplatesMissing, GitHomeTemplatesExists)
from jig.commands.hints import (
    INIT_TEMPLATE_DIR_ALREADY_SET, GIT_TEMPLATES_MISSING,
    GIT_HOME_TEMPLATES_EXISTS)


class TestStickyCommand(CommandTestCase):

    """
    Test the sticky command.

    """
    command = sticky.Command

    def setUp(self):
        super(TestStickyCommand, self).setUp()

        self.mocks = {
            'create_auto_init_templates': MagicMock(),
            'set_templates_directory': MagicMock()
        }

        self._patches = []

    def _start_patches(self):
        assert len(self._patches) == 0

        for function, mock_function in self.mocks.items():
            patched = patch(
                'jig.commands.sticky.{0}'.format(function),
                new=mock_function
            )

            patched.start()
            self._patches.append(patched)

    def run_command(self, *args, **kwargs):
        """
        Make sure that our patches have started before we run a command.
        """
        self._start_patches()

        return super(TestStickyCommand, self).run_command(*args, **kwargs)

    def tearDown(self):
        for patches in self._patches:
            patches.stop()

    def test_command_succeeds(self):
        """
        Successful command returns a message that informs the user.
        """
        self.run_command()

        self.assertResults(
            u'Jig has been setup to run everytime you clone.',
            self.output)

    def test_fails_create_auto_init_templates(self):
        """
        A failure to auto-init is formatted correctly.
        """
        self.mocks['create_auto_init_templates'].side_effect = \
            JigUserDirectoryError('Error')

        with self.assertRaises(ForcedExit):
            self.run_command()

        self.assertResults(
            u'Error',
            self.error)

    def test_templates_missing(self):
        """
        No Git templates can be found.
        """
        self.mocks['create_auto_init_templates'].side_effect = \
            GitTemplatesMissing()

        with self.assertRaises(ForcedExit):
            self.run_command()

        self.assertResults(
            result_with_hint(
                u'Unable to find templates.',
                GIT_TEMPLATES_MISSING),
            self.error)

    def test_home_templates_exist(self):
        """
        A templates directory already exists in ~/.jig/git
        """
        self.mocks['create_auto_init_templates'].side_effect = \
            GitHomeTemplatesExists('~/.jig/git/templates')

        with self.assertRaises(ForcedExit):
            self.run_command()

        self.assertResults(
            result_with_hint(
                u'~/.jig/git/templates already exists',
                GIT_HOME_TEMPLATES_EXISTS),
            self.error)

    def test_init_templatesdir_already_set(self):
        """
        Git is already configured with a init.templatedir
        """
        self.mocks['set_templates_directory'].side_effect = \
            InitTemplateDirAlreadySet('/tmp/templates')

        with self.assertRaises(ForcedExit):
            self.run_command()

        self.assertResults(
            result_with_hint(
                u'Git configuration for init.templatedir is /tmp/templates',
                INIT_TEMPLATE_DIR_ALREADY_SET),
            self.error)

    def test_git_config_error(self):
        """
        A failure to read or write to the Git config.
        """
        self.mocks['set_templates_directory'].side_effect = \
            GitConfigError(git.error(
                'git config', '', 'error'))

        with self.assertRaises(ForcedExit):
            self.run_command()

        self.assertResults(
            u'Problem when running git config: error',
            self.error)
