import os
import abc

import param

from ...util import listify, format_json_options, uuid
from ...static import DatasetStatus, DatasetSource, UriType


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

    def _create_new_dataset(self, old_dataset, dataset_name=None, dataset_metadata=None,
                            geometry=None, catalog_entry_metadata=None, ext=''):
        """Helper method for creating a new dataset and catalog entry based off of another dataset

        Args:
            dataset_name:

        Returns:

        """
        from ...api import get_metadata, update_metadata, new_dataset, new_catalog_entry, active_db

        orig_metadata = get_metadata(old_dataset)[old_dataset]
        collection = orig_metadata['collection']

        geom_type = geom_coords = None
        if geometry is None:
            orig_catalog_entry = orig_metadata['catalog_entry']
            geometry = get_metadata(orig_catalog_entry)[orig_catalog_entry]['geometry']
        elif isinstance(geometry, (list, tuple)):
            geom_type, geom_coords = geometry
            geometry = None

        catalog_entry = new_catalog_entry(
            geometry=geometry,
            geom_type=geom_type,
            geom_coords=geom_coords,
            metadata=catalog_entry_metadata,
        )

        dataset_name = dataset_name or self._create_new_dataset_name()
        display_name = '{}-{}'.format(self._name, dataset_name[:7])
        description = 'Created by tool {}'.format(self.name)

        # generate new dataset file path
        project_path = os.path.dirname(active_db())
        file_path = os.path.join(project_path, collection, dataset_name + ext)

        dataset_name = new_dataset(
            catalog_entry=catalog_entry,
            collection=collection,
            source=DatasetSource.DERIVED,
            name=dataset_name,
            display_name=display_name,
            description=description,
            file_path=file_path,
        )

        if dataset_metadata is not None:
            update_metadata(dataset_name, quest_metadata=dataset_metadata)

        return dataset_name, file_path, catalog_entry

    @staticmethod
    def _create_new_dataset_name():
        return uuid('dataset')
