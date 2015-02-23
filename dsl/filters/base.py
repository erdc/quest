import abc

class FilterBase(object):
    """Base class for data filters
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.register()


    @abc.abstractmethod
    def register(self):
        """Register plugin by setting filter name, geotype and uid 
        """


    # @abc.abstractmethod
    # def get_locations(self, *args, **kwargs):
    #     """Take a series of query parameters and return a list of 
    #     locations.
    #     """