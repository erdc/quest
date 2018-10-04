import os
import json

import pandas as pd
import matplotlib.pyplot as plt

from quest.plugins import IoBase
from quest.util.log import logger
from quest.util import setattr_on_dataframe


class XYHdf5(IoBase):
    name = 'xy-hdf5'

    def register(self):
        """Register plugin by setting description and io type."""
        self.description = 'Hdf5 for XY datasets '
        self.iotype = 'XYdata'

    def read(self, path):
        """Read metadata and dataframe from HDF5 store."""

        with pd.HDFStore(path) as h5store:
            dataframe = h5store.get('dataframe')
            setattr_on_dataframe(dataframe, 'metadata', h5store.get_storer('dataframe').attrs.metadata)
        return dataframe

    def write(self, file_path, dataframe, metadata):
        """"Write dataframe and metadata to HDF5 store."""
        base, fname = os.path.split(file_path)

        os.makedirs(base, exist_ok=True)
        with pd.HDFStore(file_path) as h5store:
            h5store.put('dataframe', dataframe)
            h5store.get_storer('dataframe').attrs.metadata = metadata

        logger.info('file written to: %s' % file_path)

    def open(self, path, fmt=None):
        dataframe = self.read(path)

        if fmt == None or fmt.lower() == 'dataframe':
            return dataframe

        # # convert index to datetime in case it is a PeriodIndex
        # dataframe.index = dataframe.index.to_datetime()
        jstr = json.loads(dataframe.to_json())
        d = dict()
        d['data'] = {k: sorted(v.items()) for k, v in jstr.items()}
        d['metadata'] = dataframe.metadata

        if fmt.lower() == 'dict':
            return d

        if fmt.lower() == 'json':
            return json.dumps(d)

        raise NotImplementedError('format %s not recognized' % fmt)

    def visualize(self, path, title, engine='mpl', start=None, end=None, **kwargs):
        """Visualize timeseries dataset."""
        if engine is not 'mpl':
            raise NotImplementedError

        df = self.read(path)
        parameter = df.metadata['parameter']

        if start is None:
            start = df.index[0]

        if end is None:
            end = df.index[-1]

        plt.style.use('ggplot')
        fig = plt.figure()
        ax = df[parameter][start:end].plot(legend=True, figsize=(8, 6))
        ax.set_title(title)
        ax.set_ylabel(df.metadata['unit'])
        base, ext = os.path.splitext(path)
        visualization_path = base + '.png'
        plt.savefig(visualization_path)
        plt.close(fig)

        return visualization_path

    def visualize_options(self, path, fmt='json'):
        """visualation options for timeseries datasets"""
        df = self.read(path)
        start = df.index[0]
        end = df.index[-1]

        schema = {
            "title": "XYDataset Vizualization Options",
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
