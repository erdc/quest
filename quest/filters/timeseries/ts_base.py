from ..base import FilterBase
from quest.api import get_metadata, new_dataset, update_metadata
from quest.api.datasets import DatasetStatus
from quest import util
import os
import param


class TsBase(FilterBase):
    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to apply filter to.""",
                                         filters={'datatype': 'timeseries'},
                                         )

    def register(self, name=None):
        """Register Timeseries

        """
        # self.name = name
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

    def _apply_filter(self):



        # if len(datasets) > 1:
        #     raise NotImplementedError('This filter can only be applied to a single dataset')

        # dataset = datasets[0]

        dataset = self.dataset

        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        orig_metadata = get_metadata(dataset)[dataset]
        if orig_metadata['file_path'] is None:
            raise IOError('No data file available for this dataset')

        df = io.read(orig_metadata['file_path'])

        # run filter
        new_df = self._apply(df)

        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'unit': new_df.metadata.get('unit'),
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
            'options': self.options,
            'status': DatasetStatus.FILTERED,
            'message': 'TS Filter Applied'
        }

        new_dset = new_dataset(orig_metadata['feature'],
                               source='derived',
                               display_name=self.display_name,
                               description=self.description,
                               )

        # save dataframe
        file_path = os.path.split(orig_metadata['file_path'])[0]
        file_path = os.path.join(file_path, new_dset)
        io.write(file_path, new_df, new_metadata)

        new_metadata.update({'file_path': file_path})
        update_metadata(new_dset, quest_metadata=new_metadata)

        return {'datasets': new_dset}

    # def apply_filter_options(self, fmt, **kwargs):
    #     schema = {}
    #
    #     return schema

    def _apply(self, df):
        raise NotImplementedError
