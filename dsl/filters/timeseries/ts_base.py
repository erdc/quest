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
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
            },
            'produces': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
            },
        }


    def apply_filter(self, datasets, features=None, options=None,
                     display_name=None, description=None, metadata=None):

        if len(util.listify(datasets)) > 1:
            raise NotImplementedError('Filter can only be applied to a single dataset')

        dataset = datasets

        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        metadata = get_metadata(dataset)[dataset]
        if metadata['_save_path'] is None:
            raise IOError('No data file available for this dataset')

        df = io.read(metadata['_save_path'])


        #apply transformation
        if options is None:
            options = {}

        # run filter
        new_df = self._apply(df, options)

        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'datatype': metadata['_datatype'],
            'filter_applied': self.name,
            'filter_options': options,
            'parent_datasets': dataset,
            'feature': metadata['_feature'],
            'file_format': metadata['_file_format'],
            'timezone': new_df.metadata.get('timezone'),
            'units': new_df.metadata.get('units'),
        }

        new_dset = new_dataset(metadata['_feature'],
                               dataset_type='derived',
                               metadata=new_metadata)

        if display_name is None:
            display_name = ''

        if description is None:
            description = 'TS Filter'

        # save dataframe
        save_path = os.path.split(metadata['_save_path'])[0]
        save_path = os.path.join(save_path, new_dset)
        io.write(save_path, new_df, new_metadata)

        new_metadata.update({'save_path': save_path})
        metadata = update_metadata(new_dset,
                                   display_name=display_name,
                                   description=description,
                                   dsl_metadata=new_metadata,
                                   metadata=metadata)

        return metadata

    def apply_filter_options(self, **kwargs):
        schema = {}

        return schema

    def _apply(df, metadata, options):
        raise NotImplementedError
