"""Base Class for I/O plugins


"""
import abc

class IoBase(object):
    """Base class for I/O for different file formats
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.register()


    @abc.abstractmethod
    def register(self):
        """Register plugin by setting description and io type 
        """

    @abc.abstractmethod
    def read_features(self, filters=None):
        """Read data from format
        """

    @abc.abstractmethod
    def read_data(self):
        """Write data to format
        """