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
        """Register plugin by setting filter name, geotype and uid 
        """

    def read(self):
        """Read data from format
        """

    def write(self):
        """Write data to format
        """