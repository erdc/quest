"""Base Class for I/O plugins


"""
from builtins import object
import abc
from future.utils import with_metaclass


class IoBase(with_metaclass(abc.ABCMeta, object)):
    """Abstract Base class for I/O for different file formats."""

    def __init__(self):
        """Init calls register."""
        self.register()

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting description and io type."""

    @abc.abstractmethod
    def read(self):
        """Write data to format."""

    @abc.abstractmethod
    def write(self):
        """Write data to format."""

    @abc.abstractmethod
    def vizualize(self):
        """Lightweight vizualization."""

    @abc.abstractmethod
    def vizualize_options(self):
        """Lightweight vizualization options."""
