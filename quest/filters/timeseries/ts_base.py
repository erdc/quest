from ..base import FilterBase
from quest.api import get_metadata, new_dataset, update_metadata
from quest import util
import os

class TsBase(FilterBase):
    def register(self, name=None):
        """Register Timeseries

        """
        self.name = name
        self.metadata = {
            'group': 'Timeseries',
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': None,
                'parameters': None,
            },
            'produces': {
                'datatype': ['timeseries'],
                'geotype': None,
                'parameters': None,
            },
        }


    def apply_filter(self, datasets, features=None, options=None,
                     display_name=None, description=None, metadata=None):

        if len(datasets) > 1:
            raise NotImplementedError('This filter can only be applied to a single dataset')

        dataset = datasets[0]

        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        orig_metadata = get_metadata(dataset)[dataset]
        if orig_metadata['file_path'] is None:
            raise IOError('No data file available for this dataset')

        df = io.read(orig_metadata['file_path'])

        #apply transformation
        if options is None:
            options = {}

        # run filter
        new_df = self._apply(df, options)

        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'datatype': orig_metadata['datatype'],
            'parent_datasets': {'dataset':dataset, 'filter_applied': self.name, 'filter_options': options},
            'file_format': orig_metadata['file_format'],
            'unit': new_df.metadata.get('unit'),
        }

        if description is None:
            description = 'TS Filter Applied'

        new_dset = new_dataset(orig_metadata['feature'],
                               source='derived',
                               display_name=display_name,
                               description=description)

        # save dataframe
        file_path = os.path.split(orig_metadata['file_path'])[0]
        file_path = os.path.join(file_path, new_dset)
        io.write(file_path, new_df, new_metadata)

        new_metadata.update({'file_path': file_path})
        update_metadata(new_dset, quest_metadata=new_metadata, metadata=metadata)

        return {'datasets': new_dset}

    def apply_filter_options(self, fmt, **kwargs):
        schema = {}

        return schema

    def _apply(df, metadata, options):
        raise NotImplementedError
