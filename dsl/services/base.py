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

        Plugins must contain a service name, provider and bounding box
        """

    @abc.abstractmethod
    def get_locations(self, locations=None, bounding_box=None, **kwargs):
        """Get Locations associated with service.

        Take a series of query parameters and return a list of 
        locations as a geojson python dictionary
        """

    @abc.abstractmethod
    def get_locations_options(self):
        """Get Filters that can be applied to get_locations call

        Response defined as JSON-Schema
        """
        
    @abc.abstractmethod
    def get_data(self, location, path=None, **kwargs):
        """Download/Transfer data associated with service

        This must either a path varable and query parameters and download 
        the data to the provided path
        """

    @abc.abstractmethod
    def get_data_options(self):
        """Get filters that can be applied to the get_data call

        Response defined as JSON-Schema
        """

    @abc.abstractmethod
    def provides(self, bounding_box=None, **kwargs):
        """List parameters that the service potentially provides

        """