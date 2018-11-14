from quest import util
from quest.plugins import ToolBase
from quest.api import get_metadata
from quest.plugins import load_plugins
from quest.static import UriType, DataType


class TsBase(ToolBase):
    # metadata attributes
    group = 'Timeseries'
    operates_on_datatype = [DataType.TIMESERIES]
    operates_on_geotype = None
    operates_on_parameters = None
    produces_datatype = [DataType.TIMESERIES]
    produces_geotype = None
    produces_parameters = None

    dataset = util.param.DatasetSelector(default=None,
                                         doc="""Dataset to apply filter to.""",
                                         filters={'datatype': DataType.TIMESERIES},
                                         )

    def _run_tool(self):
        dataset = self.dataset

        io = load_plugins('io', 'timeseries-hdf5')['timeseries-hdf5']
        orig_metadata = get_metadata(dataset)[dataset]
        if orig_metadata['file_path'] is None:
            raise IOError('No data file available for this dataset')

        df = io.read(orig_metadata['file_path'])

        # run filter
        new_df = self._run(df)


        # setup new dataset
        new_metadata = {
            'parameter': new_df.metadata.get('parameter'),
            'unit': new_df.metadata.get('unit'),
            'datatype': orig_metadata['datatype'],
            'file_format': orig_metadata['file_format'],
        }

        new_dset, file_path, catalog_entry = self._create_new_dataset(
            old_dataset=dataset,
            ext='.h5',
            dataset_metadata=new_metadata,
        )

        # save dataframe
        io.write(file_path, new_df, new_metadata)

        return {'datasets': new_dset}

    def _run(self, df):
        raise NotImplementedError
