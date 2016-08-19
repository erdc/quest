"""io plugin for timeseries datasets."""

import os
import pandas as pd
import rasterio

from .base import IoBase


class Nrmm(IoBase):
    """NetCDF IO for timeseries using xarray."""

    def register(self):
        "Register plugin by setting description and io type."
        self.description = 'NRMM Reader'
        self.iotype = 'nrmm'

    def read(self, path):
        "Read metadata and raster from nrmm dataset."
        if not path.endswith('asc'):
            if os.path.isdir(path):
                path = os.path.join(path, 'nrmm') # nrmm datasets created by vitd2nrmm are (nrmm.asc, nrmm.prj, nrmm.txt)
            grid_filename = path + '.asc'
            attr_filename = path + '.txt'
        else:
            grid_filename = path
            base, _ = os.path.splitext(path)
            attr_filename = base + '.txt'

        with rasterio.open(grid_filename) as src:
            grid = src.read()

        attrs = pd.read_table(attr_filename, skiprows=8)
        return grid, attrs, src.meta.copy()

    def write(self, save_path, dataframe, metadata):
        "Write nrmm file"
        raise NotImplementedError('NRMM write not available')

    def open(self, path, fmt=None):
        raise NotImplementedError('NRMM open fn not available')

    def visualize(self, path, title, theme, **kwargs):
        """Visualize nrmm dataset."""

        grid, attrs, src_meta = self.read(path)
        theme_dict = {
            'Slope': ('slope', 'GRADE'),
            'USCS Soil Type': ('soil_type', 'KUSCS'),
            'Soil Strength': ('soil_strength', 'RCIC(1)'),
        }

        parameter, col = theme_dict[theme]
        keys = attrs[col].values
        new_raster = keys[grid-1]

        out_meta = src_meta
        # save the resulting raster
        dst = os.path.join(path, '{}.tif'.format(parameter))
        new_raster = new_raster.astype('int16')
        out_meta.update({"driver": "GTiff", 'dtype': new_raster.dtype})
        with rasterio.open(dst, 'w', **out_meta) as dest:
            dest.write(new_raster)

        return dst

    def visualize_options(self, path, fmt='json-schema'):
        """visualization options for nrmm datasets"""

        if fmt=='smtk':
            return ''

        schema = {
            "title": "NRMM Vizualization Options",
            "type": "object",
            "properties": {
                "theme": {
                    "type": {"enum":['Slope', 'USCS Soil Type', 'Soil Strength'], 'default': 'Slope'},
                    "description": "NRMM theme to visualize",
                },
            },
        }

        return schema
