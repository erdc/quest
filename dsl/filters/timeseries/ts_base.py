from ..base import FilterBase
from dsl.api import get_metadata, new_dataset

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


    def apply_filter(self, datasets, features=None, options=None):

        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        metadata = get_metadata(dataset)
        if metadata['_save_path'] is None:
            raise IOError('No data file available for this dataset')

        df = io.read(metadata['_save_path'])


        #apply transformation
        new_df = self._apply(df, options)

        new_metadata = {
            '_parameter': new_df.parameter,
            '_dataset_type': 'derived',
            '_datatype': metadata['datatype'],
            '_filter_applied': self.name,
            '_parent_dataset': dataset,
            '_feature': metadata['_feature'],
            '_file_format': metadata['_file_format']
            'timezone': new_df.tz,
            'units': new_df.units,
        }

        # setup new dataset
        display_name = options.get('display_name')
        if display_name is None:
            display_name = ''

        description = options.get('description')
        if description is None:
            description = 'TS Filter'

        new_dset = new_dataset(metadata['_feature'],
                               dataset_type='derived',
                               display_name=display_name,
                               description=description,
                               metadata=new_metadata)

        save_path = os.path.split(metadata['_save_path'])[0]
        save_path = os.path.join(save_path, new_dset)
        new_metadata.update({'save_path': save_path})
        io.write(save_path, new_df, new_metadata)
        metadata = update_metadata(new_dset, metadata={'save_path':save_path})

        return metadata

    def apply_filter_options(self, **kwargs):
        schema = {}

        return schema

    def _apply(df, metadata, options):
        raise NotImplementedError
