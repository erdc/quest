from ..base import FilterBase
from quest.api import get_metadata, new_dataset, update_metadata
from quest import util
import os


class TsFlowDuration(FilterBase):
    def register(self, name='flowDuration'):
        """Register Timeseries

        """
        self.name = name
        self.metadata = {
            'group': 'Timeseries: Flow Duration',
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': None,
                'parameters': 'streamflow',
            },
            'produces': {
                'datatype': ['timeseries'],
                'geotype': None,
                'parameters': 'streamflow',
            },
        }

    def _apply_filter(self, datasets, features=None, options=None,
                      display_name=None, description=None, metadata=None):

        if len(datasets) > 1:
            raise NotImplementedError('This filter can only be applied to a single dataset')

        dataset = datasets[0]

        input = util.load_drivers('io', 'timeseries-hdf5')
        input = input['timeseries-hdf5'].driver
        orig_metadata = get_metadata(dataset)[dataset]
        if orig_metadata['file_path'] is None:
            raise IOError('No data file available for this dataset')

        df = input.read(orig_metadata['file_path'])

        # apply transformation
        if options is None:
            options = {}

        # run filter
        # new_df = self._apply(df, options)
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']
        df.sort_values(['streamflow'], ascending=False, na_position='last', inplace=True)
        df['Rank'] = df['streamflow'].rank(method='min', ascending=False)
        df.dropna(inplace=True)
        df['Percent Exceeded'] = (df['Rank'] / (df['streamflow'].count() + 1)) * 100
        df.index = df['Percent Exceeded']

        df.metadata = metadata
        new_df = df
        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'datatype': orig_metadata['datatype'],
            'options': self.options,
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
        save_path = os.path.split(orig_metadata['file_path'])[0]
        save_path = os.path.join(save_path, new_dset)
        output = util.load_drivers('io', 'xyHdf5')
        output = output['xyHdf5'].driver
        output.write(save_path, new_df, new_metadata)

        new_metadata.update({'file_path': save_path})
        update_metadata(new_dset, quest_metadata=new_metadata)

        return {'datasets': new_dset}

    def apply_filter_options(self, fmt, **kwargs):
        schema = {
            "title": "Flow Duration",
            "type": "object",
            "properties": {}
        }

        return schema

    def _apply(df, metadata, options):
        raise NotImplementedError