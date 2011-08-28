from becareful.tests.testcase import BeCarefulTestCase


class TestAddingHook(BeCarefulTestCase):

    """
    Can we properly hook a Git repository

    """
    def test_will_stop_if_pre_commit_exists(self):
        """
        Stop if .git/hooks/pre-commit exists
        """
        pass
