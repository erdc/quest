import json

from quest.static import DataType
from quest_io_plugins.xyHdf5 import XYHdf5


class TsHdf5(XYHdf5):
    """NetCDF IO for timeseries using xarray."""
    name = 'timeseries-hdf5'

    def register(self):
        "Register plugin by setting description and io type."
        self.description = 'HDF5 IO for Timeseries datasets'
        self.iotype = 'timeseries'

    def open(self, path, fmt=None):
        dataframe = self.read(path)

        if fmt is None or fmt.lower() == 'dataframe':
            return dataframe

        # convert index to datetime in case it is a PeriodIndex
        dataframe.index = dataframe.index.to_datetime()
        jstr = json.loads(dataframe.to_json(date_format='iso'))
        d = dict()
        d['data'] = {k: sorted(v.items()) for k, v in jstr.items()}
        d['metadata'] = dataframe.metadata

        if fmt.lower() == 'dict':
            return d

        if fmt.lower() == 'json':
            return json.dumps(d)

        raise NotImplementedError('format %s not recognized' % fmt)

    def visualize_options(self, path, fmt='json'):
        """visualation options for timeseries datasets"""
        df = self.read(path)
        start = df.index[0].strftime('%Y-%m-%d %H:%M:%S')
        end = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')

        schema = {
            "title": "Timeseries Vizualization Options",
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "description": "start date",
                    "default": start,
                },
                "end": {
                    "type": "string",
                    "description": "end date",
                    "default": end,
                },
            },
        }

        return schema
