from quest.plugins import ToolBase
from quest.api import get_metadata, new_dataset, update_metadata
from quest import util
from quest.plugins import load_plugins
import os


class TsFlowDuration(ToolBase):
    _name = 'flow-duration'
    group = 'Timeseries'

    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to apply filter to.""",
                                         filters={'datatype': 'timeseries'},
                                         )

    def _run_tool(self):

        dataset = self.dataset

        input = load_plugins('io', 'timeseries-hdf5')['timeseries-hdf5']
        orig_metadata = get_metadata(dataset)[dataset]
        if orig_metadata['file_path'] is None:
            raise IOError('No data file available for this dataset')

        df = input.read(orig_metadata['file_path'])

        # apply transformation

        # run filter
        # new_df = self._run(df, options)
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
            'options': self.set_options,
            'file_format': orig_metadata['file_format'],
            'unit': new_df.metadata.get('unit'),
        }

        new_dset = new_dataset(orig_metadata['feature'],
                               source='derived',
                               # display_name=self.display_name,
                               description=self.description)

        self.set_display_name(new_dset)

        # save dataframe
        save_path = os.path.split(orig_metadata['file_path'])[0]
        save_path = os.path.join(save_path, new_dset)
        output = load_plugins('io', 'xy-hdf5')['xy-hdf5']
        output.write(save_path, new_df, new_metadata)

        new_metadata.update({'file_path': save_path})
        update_metadata(new_dset, quest_metadata=new_metadata)

        return {'datasets': new_dset}