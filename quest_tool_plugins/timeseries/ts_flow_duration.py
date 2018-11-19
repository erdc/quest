from quest import util
from quest.plugins import ToolBase
from quest.api import get_metadata
from quest.static import DataType, UriType
from quest.plugins import load_plugins
from quest.util import setattr_on_dataframe


class TsFlowDuration(ToolBase):
    _name = 'flow-duration'
    group = 'Timeseries'

    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to apply filter to.""",
                                         filters={'datatype': DataType.TIMESERIES},
                                         )

    def _run_tool(self):

        dataset = self.dataset

        input_ts = load_plugins('io', 'timeseries-hdf5')['timeseries-hdf5']
        orig_metadata = get_metadata(dataset)[dataset]
        parameter = orig_metadata['parameter']
        if orig_metadata['file_path'] is None:
            raise IOError('No data file available for this dataset')

        df = input_ts.read(orig_metadata['file_path'])

        # apply transformation

        # run filter
        # new_df = self._run(df, options)
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']
        df.sort_values([parameter], ascending=False, na_position='last', inplace=True)
        df['Rank'] = df[parameter].rank(method='min', ascending=False)
        df.dropna(inplace=True)
        df['Percent Exceeded'] = (df['Rank'] / (df[parameter].count() + 1)) * 100
        df.index = df['Percent Exceeded']

        setattr_on_dataframe(df, 'metadata', metadata)
        new_df = df
        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'datatype': orig_metadata['datatype'],
            'options': self.set_options,
            'file_format': orig_metadata['file_format'],
            'unit': new_df.metadata.get('unit'),
        }

        new_dset, file_path, catalog_entry = self._create_new_dataset(
            old_dataset=dataset,
            ext='.h5',
            dataset_metadata=new_metadata,
        )

        # save dataframe
        output = load_plugins('io', 'xy-hdf5')['xy-hdf5']
        output.write(file_path, new_df, new_metadata)

        return {'datasets': new_dset, 'catalog_entries': catalog_entry}
