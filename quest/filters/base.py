from builtins import object
import abc

import param
from future.utils import with_metaclass

from ..util import listify, format_json_options
from ..api.metadata import update_metadata
from ..api.datasets import DatasetStatus


class FilterBase(param.Parameterized):
    """Base class for data filters."""
    _name = None
    name = param.String(default='Filter', precedence=-1)

    def __init__(self, **params):
        params.update({'name': self._name})
        self.register()
        self._filter_options = None
        super(FilterBase, self).__init__(**params)

    @property
    def title(self):
        return '{} Options'.format(self.name.replace('-', ' ').title())

    @property
    def display_name(self):
        return 'Created by filter {}'.format(self.name)

    @property
    def description(self):
        return '{} Filter Applied'.format(self.metadata['group'].capitalize)

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting filter name, geotype and uid."""
        pass

    def apply_filter(self, **options):
        """Function that applies filter"""
        self.set_param(**options)

        self._filter_options = options
        result = self._apply_filter()
        datasets = listify(result.get('datasets', []))
        for dataset in datasets:
            update_metadata(dataset, quest_metadata={
                'options': self.options,
                'status': DatasetStatus.FILTERED
            })

        return result

    @abc.abstractmethod
    def _apply_filter(self, **options):
        """Function that applies filter"""
        pass

    def apply_filter_options(self, fmt=None):
        """Function that applies filter"""

        if fmt == 'json-schema':
            return format_json_options(self)

        return self

    @property
    def options(self):
        return {'filter_applied': self.name,
                'filter_options': self._filter_options
                }
