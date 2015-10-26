from builtins import object
import abc
from future.utils import with_metaclass

class FilterBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data filters
    """

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