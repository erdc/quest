from builtins import object
import abc
import param
from future.utils import with_metaclass
from quest.static import DatasetStatus
from quest.util import listify, format_json_options, build_smtk


class FilterBase(param.Parameterized):
    """Base class for data filters."""
    _name = None
    # name = param.String(default='Filter', precedence=-1)
    smtk_template = None

    # metadata attributes
    group = None
    operates_on_datatype = None
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = None
    produces_geotype = None
    produces_parameters = None

    def __init__(self, **params):
        params.update({'name': self._name})
        # self.register()
        self._filter_options = None
        super(FilterBase, self).__init__(**params)

    @property
    def metadata(self):
        return {
            'group': self.group,
            'operates_on': {
                'datatype': self.operates_on_datatype,
                'geotype': self.operates_on_geotype,
                'parameters': self.operates_on_parameters,
            },
            'produces': {
                'datatype': self.produces_datatype,
                'geotype': self.produces_geotype,
                'parameters': self.produces_parameters,
            },
        }

    @property
    def title(self):
        return '{} Options'.format(self.name.replace('-', ' ').title())

    @property
    def description(self):
        return 'Created by filter {}'.format(self.name)

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting filter name, geotype and uid."""
        pass

    def set_display_name(self, dataset):
        from quest.api.metadata import update_metadata
        display_name = '{}-{}'.format(self._name, dataset[:7])
        update_metadata(dataset, display_name=display_name)

    def apply_filter(self, **options):
        from quest.api.metadata import update_metadata
        """Function that applies filter"""
        options.pop('name', None)
        self.set_param(**options)

        self._filter_options = options or dict(self.get_param_values())
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

    def apply_filter_options(self, fmt, **kwargs):
        """Function that applies filter"""
        kwargs.pop('name', None)
        self.set_param(**kwargs)

        if fmt == 'param':
            schema = self

        elif fmt == 'smtk':
            if self.smtk_template is None:
                return ''
            schema = build_smtk('filter_options',
                                self.smtk_template)

        elif fmt == 'json':
            schema = format_json_options(self)

        else:
            raise ValueError('{} is an unrecognized format.'.format(fmt))

        return schema

    @property
    def options(self):
        return {'filter_applied': self.name,
                'filter_options': self._filter_options
                }
