"""
Collection of :py:class:`Exception` subclasses used by jig.
"""


class jigException(Exception):

    """
    Base exception.

    """
    pass


class ForcedExit(jigException):

    """
    Raised when execution of should stop.

    This exception is useful in testing. Typically the runner is configured to
    not ``sys.exit()`` on exception so this object can be used in its place.

    """
    pass


class NotGitRepo(jigException):

    """
    A directory provided does not appear to be a Git repository.

    """
    pass


class PreCommitExists(jigException):

    """
    The :file:`pre-commit` file in the hooks directory exists.

    """
    pass


class GitRepoNotInitialized(jigException):

    """
    The given Git repository has not been initialized for usage.

    """
    pass


class AlreadyInitialized(jigException):

    """
    The given Git repository has been initialized already.

    """
    pass


class PluginError(jigException):

    """
    An error occured while working with a plugin.

    """
    pass


class CommandError(jigException):

    """
    Raise when an error occurs while using any command line tool.

    """
    pass


class ExpectationError(jigException):

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
