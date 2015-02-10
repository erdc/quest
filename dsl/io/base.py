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
    def read(self):
        """Read data from format
        """

    @abc.abstractmethod
    def write(self):
        """Write data to format
        """