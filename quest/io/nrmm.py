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
            profile = src.profile
            profile.update(dtype=rasterio.uint8, driver='GTiff', count=1, compress='lzw')

        attrs = pd.read_table(attr_filename, skiprows=8)

        return grid, attrs, profile.copy()

    def write(self, file_path, dataframe, metadata):
        "Write nrmm file"
        raise NotImplementedError('NRMM write not available')

    def open(self, path, fmt=None):
        raise NotImplementedError('NRMM open fn not available')

    def visualize(self, path, title, theme, plot_format='geotiff', **kwargs):
        """Visualize nrmm dataset."""

        grid, attrs, profile = self.read(path)
        theme_dict = {
            'Slope': ('slope', 'GRADE'),
            'USCS Soil Type': ('soil_type', 'KUSCS'),
            'Soil Strength': ('soil_strength', 'RCIC(1)'),
        }

        # remap raster according to theme dict
        parameter, col = theme_dict[theme]
        keys = attrs[col].values
        new_raster = keys[grid-1]

        if plot_format.lower() =='png':
            import matplotlib.pylab as plt
            plt.style.use('ggplot')
            fig = plt.figure()
            plt.imshow(new_raster.squeeze())
            dst = os.path.join(path, '{}.png'.format(parameter))
            plt.savefig(dst)
            plt.close(fig)
        else:
            # save the resulting raster
            dst = os.path.join(path, '{}.tif'.format(parameter))
            new_raster = new_raster.astype(rasterio.uint8)
            with rasterio.open(dst, 'w', **profile) as dest:
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
                "plot_format": {
                    "type": {"enum":['png', 'geotiff'], 'default': 'geotiff'},
                    "description": "output format",
                },
            },
        }

        return schema
