import abc

class DataServiceBase(object):
    """Base class for data services plugins
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.register()


    @abc.abstractmethod
    def register(self):
        """Register plugin

        Plugins must contain a service name, source and bounding box
        """


    @abc.abstractmethod
    def get_locations(self, *args, **kwargs):
        """Get Locations associated with service.

        Take a series of query parameters and return a list of 
        locations.
        """

    @abc.abstractmethod
    def get_data(self, *args, **kwargs):
        """Download/Transfer data associated with service
        """