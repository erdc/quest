from ..base import FilterBase
from dsl.api import get_metadata, new_dataset, update_metadata
from dsl import util
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
        if orig_metadata['_save_path'] is None:
            raise IOError('No data file available for this dataset')

        df = io.read(orig_metadata['_save_path'])

        #apply transformation
        if options is None:
            options = {}

        # run filter
        new_df = self._apply(df, options)

        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'datatype': orig_metadata['_datatype'],
            'filter_applied': self.name,
            'filter_options': options,
            'parent_datasets': dataset,
            'file_format': orig_metadata['_file_format'],
            'timezone': new_df.metadata.get('timezone'),
            'units': new_df.metadata.get('units'),
        }

        if description is None:
            description = 'TS Filter Applied'

        new_dset = new_dataset(orig_metadata['_feature'],
                               dataset_type='derived',
                               display_name=display_name,
                               description=description)

        # save dataframe
        save_path = os.path.split(orig_metadata['_save_path'])[0]
        save_path = os.path.join(save_path, new_dset)
        io.write(save_path, new_df, new_metadata)

        new_metadata.update({'save_path': save_path})
        metadata = update_metadata(new_dset,
                                   dsl_metadata=new_metadata,
                                   metadata=metadata)

        return metadata

    def apply_filter_options(self, **kwargs):
        schema = {}

        return schema

    def _apply(df, metadata, options):
        raise NotImplementedError
