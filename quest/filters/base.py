from builtins import object
import abc
from future.utils import with_metaclass


class FilterBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data filters."""

    def __init__(self):
        self.register()

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting filter name, geotype and uid."""
        pass

    @abc.abstractmethod
    def apply_filter(self, dataset, features, options):
        """Function that applies filter"""
        pass

    @abc.abstractmethod
    def apply_filter_options(self, fmt):
        """Function that applies filter"""
        pass
