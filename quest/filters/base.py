from builtins import object
import abc
from future.utils import with_metaclass


class FilterBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data filters."""

    def __init__(self):
        self.register()
        self._options = None
        self._datasets = None
        self._features = None
        self._filter_options = None

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting filter name, geotype and uid."""
        pass

    def apply_filter(self, datasets, features, options, *args, **kwargs):
        """Function that applies filter"""
        self._datasets = datasets
        self._features = features
        self._filter_options = options
        return self._apply_filter(datasets, features, options, *args, **kwargs)

    @abc.abstractmethod
    def _apply_filter(self, datasets, features, options):
        """Function that applies filter"""
        pass

    @abc.abstractmethod
    def apply_filter_options(self, fmt):
        """Function that applies filter"""
        pass

    @property
    def options(self):
        return {'filter_applied': self.name,
                'dataset': self._datasets,
                'features': self._features,
                'filter_options': self._filter_options
                }
