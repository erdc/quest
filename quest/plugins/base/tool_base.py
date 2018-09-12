import abc
import param
from quest.static import DatasetStatus
from quest.util import listify, format_json_options


class ToolBase(param.ParameterizedFunction):
    """Base class for data tools."""
    _name = None

    # metadata attributes
    group = None
    operates_on_datatype = None
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = None
    produces_geotype = None
    produces_parameters = None

    @param.parameterized.bothmethod
    def instance(self, **params):
        inst = super(ToolBase, self).instance(name=self._name, **params)
        self._set_options = None
        return inst

    def __call__(self, **kwargs):
        return self.run_tool(**kwargs)

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
        return 'Created by tool {}'.format(self.name)

    @property
    def set_options(self):
        return {'tool_applied': self.name,
                'tool_options': self._set_options
                }

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting tool name, geotype and uid."""
        pass

    def set_display_name(self, dataset):
        from quest.api.metadata import update_metadata
        display_name = '{}-{}'.format(self._name, dataset[:7])
        update_metadata(dataset, display_name=display_name)

    def run_tool(self, **options):
        from quest.api.metadata import update_metadata
        """Function that applies tools"""
        options.pop('name', None)
        self.set_param(**options)

        self._set_options = options or dict(self.get_param_values())
        result = self._run_tool()
        datasets = listify(result.get('datasets', []))
        catalog_entries = listify(result.get('catalog_entries', []))
        for dataset in datasets:
            update_metadata(dataset, quest_metadata={
                'options': self.set_options,
                'status': DatasetStatus.DERIVED
            })

        result.update(datasets=datasets, catalog_entries=catalog_entries)

        return result

    @abc.abstractmethod
    def _run_tool(self, **options):
        """Function that applies tools"""
        pass

    def get_tool_options(self, fmt, **kwargs):
        """Function that applies tools"""
        kwargs.pop('name', None)
        self.set_param(**kwargs)

        if fmt == 'param':
            schema = self

        elif fmt == 'json':
            schema = format_json_options(self)

        else:
            raise ValueError('{} is an unrecognized format.'.format(fmt))

        return schema
