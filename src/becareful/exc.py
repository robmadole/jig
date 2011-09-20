"""
Collection of :py:class:`Exception` subclasses used by BeCareful.
"""


class BeCarefulException(Exception):

    """
    Base exception.

    """
    pass


class NotGitRepo(BeCarefulException):

    """
    A directory provided does not appear to be a git repository.

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
