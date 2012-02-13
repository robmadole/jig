"""
Collection of :py:class:`Exception` subclasses used by BeCareful.
"""


class BeCarefulException(Exception):

    """
    Base exception.

    """
    pass


class ForcedExit(BeCarefulException):

    """
    Raised when execution of should stop.

    This exception is useful in testing. Typically the runner is configured to
    not ``sys.exit()`` on exception so this object can be used in its place.

    """
    pass


class NotGitRepo(BeCarefulException):

    """
    A directory provided does not appear to be a Git repository.

    """
    pass


class PreCommitExists(BeCarefulException):

    """
    The :file:`pre-commit` file in the hooks directory exists.

    """
    pass


class GitRepoNotInitialized(BeCarefulException):

    """
    The given Git repository has not been initialized for usage.

    """
    pass


class AlreadyInitialized(BeCarefulException):

    """
    The given Git repository has been initialized already.

    """
    pass


class PluginError(BeCarefulException):

    """
    An error occured while working with a plugin.

    """
    pass


class CommandError(BeCarefulException):

    """
    Raise when an error occurs while using any command line tool.

    """
    pass


class ExpectationError(BeCarefulException):

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
