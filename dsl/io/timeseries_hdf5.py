"""io plugin for timeseries datasets."""

import os
import pandas as pd

from .base import IoBase
from .. import util


class TsHdf5(IoBase):
    "NetCDF IO for timeseries using xarray."

    def register(self):
        "Register plugin by setting description and io type."

        self.description = 'HDF5 IO for Timeseries datasets'
        self.iotype = 'timeseries'

    def read(self, path):
        "Read metadata and dataframe from HDF5 store."

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
