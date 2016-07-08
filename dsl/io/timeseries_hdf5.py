"""io plugin for timeseries datasets."""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt

from .base import IoBase
from .. import util


class TsHdf5(IoBase):
    """NetCDF IO for timeseries using xarray."""

    def register(self):
        "Register plugin by setting description and io type."
        self.description = 'HDF5 IO for Timeseries datasets'
        self.iotype = 'timeseries'

    def read(self, path):
        "Read metadata and dataframe from HDF5 store."
        if not path.endswith('h5'):
            path += '.h5'

        with pd.get_store(path) as h5store:
            dataframe = h5store.get('dataframe')
            dataframe.metadata = h5store.get_storer('dataframe').attrs.metadata

        return dataframe

    def write(self, save_path, dataframe, metadata):
        "Write dataframe and metadata to HDF5 store."
        base, fname = os.path.split(save_path)
        if not save_path.endswith('h5'):
            save_path += '.h5'

        util.mkdir_if_doesnt_exist(base)
        with pd.get_store(save_path) as h5store:
            h5store.put('dataframe', dataframe)
            h5store.get_storer('dataframe').attrs.metadata = metadata

        print('file written to: %s' % save_path)

    def open(self, path, fmt=None):
        dataframe = self.read(path)

        if fmt == None or fmt.lower() == 'dataframe':
            return dataframe

        # convert index to datetime in case it is a PeriodIndex
        dataframe.index = dataframe.index.to_datetime()
        d = json.loads(dataframe.to_json(date_format='iso'))
        d['metadata'] = dataframe.metadata

        if fmt.lower() == 'dict':
            return d

        if fmt.lower() == 'json':
            return json.dumps(d)

        raise NotImplementedError('format %s not recognized' % fmt)

    def vizualize(self, path, title, engine='mpl', start=None, end=None, **kwargs):
        """Vizualize timeseries dataset."""
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
        ax.set_ylabel(df.metadata['units'])
        base, ext = os.path.splitext(path)
        visualization_path = base + '.png'
        plt.savefig(visualization_path)
        plt.close(fig)

        return visualization_path

    def vizualize_options(self, path):
        """vizualation options for timeseries datasets"""
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
