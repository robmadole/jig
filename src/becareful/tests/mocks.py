from mock import Mock


class MockPlugin(Mock):

    """
    Provides mock Plugin object the emulates the real Plugin.

    """
    def __init__(self, *args, **kwargs):
        name = 'Unnamed'
        if 'name' in kwargs:
            name = kwargs['name']
            del kwargs['name']

        super(MockPlugin, self).__init__(*args, **kwargs)
        self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def _get_child_mock(self, *args, **kwargs):
        """
        Return a normal Mock instead of a MockPlugin.
        """
        return Mock(*args, **kwargs)
