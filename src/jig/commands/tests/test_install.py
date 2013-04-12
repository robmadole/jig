# coding=utf-8
from os.path import join
from textwrap import dedent

from jig.exc import ForcedExit
from jig.tests.testcase import (
    CommandTestCase, PluginTestCase, cd_gitrepo, result_with_hint)
from jig.commands.hints import USE_RUNNOW
from jig.commands import install


class TestInstallCommand(CommandTestCase, PluginTestCase):

    """
    Test the install command.

    """
    command = install.Command

    def setUp(self):
        super(TestInstallCommand, self).setUp()

        self.plugin01_dir = join(self.fixturesdir, 'plugin01')
        self.plugin02_dir = join(self.fixturesdir, 'plugin02')

    @cd_gitrepo
    def test_plugins_file_does_not_exist(self):
        """
        The specified file does not exist.
        """
        with self.assertRaises(ForcedExit):
            self.run_command('badfilename.txt')

        self.assertResults(
            'No such file or directory',
            self.error)

    @cd_gitrepo
    def test_install_local_plugin(self):
        """
        Can install a single local file system plugin.
        """
        # Create a file to store the location of plugins to install
        self.commit(
            self.gitrepodir, 'jigplugins.txt',
            self.plugin01_dir)

        self.run_command('jigplugins.txt')

        self.assertResults(
            result_with_hint(dedent(
                u'''
                From {0}:
                 - Added plugin plugin01 in bundle test01
                '''.format(self.plugin01_dir)),
                USE_RUNNOW),
            self.output)

    @cd_gitrepo
    def test_skips_duplicates(self):
        """
        If a duplicate is being installed, skips it.
        """
        self.commit(
            self.gitrepodir, 'jigplugins.txt',
            '{0}\n{0}\n'.format(self.plugin01_dir))

        self.run_command('jigplugins.txt')

        self.assertResults(
            result_with_hint(dedent(
                u'''
                From {0}:
                 - Added plugin plugin01 in bundle test01
                From {0}:
                 - The plugin is already installed.
                '''.format(self.plugin01_dir)),
                USE_RUNNOW),
            self.output)

    @cd_gitrepo
    def test_plugins_has_one_error(self):
        """
        The specified exists but the first location is a bad plugin.

        Confirms that the install continues even if an error is found.
        """
        self.commit(
            self.gitrepodir, 'jigplugins.txt',
            '{0}\n{1}\n'.format(
                self.plugin02_dir, self.plugin01_dir))

        self.run_command('jigplugins.txt')

        self.assertResults(result_with_hint(dedent(
            u'''
            From {0}:
             - File contains parsing errors: {0}/config.cfg
            \t[line  2]: 'This is a bad config file that will fail to parse\\n'
            From {1}:
             - Added plugin plugin01 in bundle test01
            '''.format(self.plugin02_dir, self.plugin01_dir)), USE_RUNNOW),
            self.output)
