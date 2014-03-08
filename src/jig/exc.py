"""
Collection of :py:class:`Exception` subclasses used by jig.
"""


class JigException(Exception):

    """
    Base exception.

    """
    def __init__(self, *args, **kwargs):
        hint = kwargs.pop('hint', None)

        super(JigException, self).__init__(*args, **kwargs)

        if hint is not None:
            self.hint = hint


class ForcedExit(JigException):

    """
    Raised when execution of should stop.

    This exception is useful in testing. Typically the runner is configured to
    not ``sys.exit()`` on exception so this object can be used in its place.

    """
    def __eq__(self, other):
        return str(self) == str(other)


class NotGitRepo(JigException):

    """
    A directory provided does not appear to be a Git repository.

    """
    hint = 'NOT_GIT_REPO'


class PreCommitExists(JigException):

    """
    The :file:`pre-commit` file in the hooks directory exists.

    """
    hint = 'PRE_COMMIT_EXISTS'


class GitRepoNotInitialized(JigException):

    """
    The given Git repository has not been initialized for usage.

    """
    hint = 'GIT_REPO_NOT_INITIALIZED'


class GitCloneError(JigException):

    """
    Attempting to clone a Git repository failed.

    """
    pass


class GitWorkingDirectoryDirty(JigException):

    """
    If the given Git repository has a non-clean working directory.

    """
    def __init__(self):
        super(GitWorkingDirectoryDirty, self).__init__(
            'The Git working directory must be clean before '
            'running this command.')


class GitRevListFormatError(JigException):

    """
    The given Git revision list is not in a valid format.

    """
    hint = 'GIT_REV_LIST_FORMAT_ERROR'


class GitRevListMissing(JigException):

    """
    The revision lists could not be found for a given Git repository.

    """
    hint = 'GIT_REV_LIST_MISSING'


class GitTemplatesMissing(JigException):

    """
    The shared Git templates directory is not in any expected locations.

    """
    hint = 'GIT_TEMPLATES_MISSING'

    def __init__(self):
        super(GitTemplatesMissing, self).__init__(
            'Unable to find templates.')


class GitHomeTemplatesExists(JigException):

    """
    The ~/.jig/templates directory already exists.

    """
    hint = 'GIT_HOME_TEMPLATES_EXISTS'

    def __init__(self, home_templates_directory):
        super(GitHomeTemplatesExists, self).__init__(
            '{0} already exists'.format(home_templates_directory)
        )


class InitTemplateDirAlreadySet(JigException):

    """
    If the Git config already has a value for the init.templatedir key.

    """
    hint = 'INIT_TEMPLATE_DIR_ALREADY_SET'

    def __init__(self, init_templatedir):
        super(InitTemplateDirAlreadySet, self).__init__(
            'Git configuration for init.templatedir is {0}'.format(
                init_templatedir))


class GitConfigError(JigException):

    """
    Raise when an error occurs reading or writing the Git config.

    """
    def __init__(self, git_command_error):
        """
        Use the stderr message from the command as this exception's message.

        :param git.exc.GitCommandError git_command_error:
        """
        super(GitConfigError, self).__init__(
            'Problem when running {0}: {1}'.format(
                git_command_error.command, git_command_error.stderr))


class AlreadyInitialized(JigException):

    """
    The given Git repository has been initialized already.

    """
    hint = 'ALREADY_INITIALIZED'


class JigUserDirectoryError(JigException):

    """
    An error finding or creating the ~/.jig directory.

    """
    pass


class PluginError(JigException):

    """
    An error occured while working with a plugin.

    """
    pass


class CommandError(JigException):

    """
    Raise when an error occurs while using any command line tool.

    """
    pass


class ConfigKeyInvalid(JigException):

    """
    Raise whenever the dot-separated config key is not valid.
    """
    hint = 'INVALID_CONFIG_KEY'


class RangeError(JigException):

    """
    Raise when a given numbered test range is invalid.

    """
    hint = 'INVALID_RANGE'


class ExpectationError(JigException):

    """
    Base class for all error dealing with plugin expectations.

    """
    pass


class ExpectationNoTests(ExpectationError):

    """
    Raise when no tests (numbered directories) are found for a plugin.

    """
    pass


class ExpectationFileNotFound(ExpectationError):

    """
    Raised when the expectation file should be present but is not.

    """
    pass


class ExpectationParsingError(ExpectationError):

    """
    Raised when errors are found while parsing reStructuredText expectations.

    """
    pass
