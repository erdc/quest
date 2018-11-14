import os
import subprocess

import rasterio
import xarray as xr

from quest.plugins import IoBase
from quest.static import DataType
from quest.util import convert_nodata_to_nans


class RasterGdal(IoBase):
    """IO for raster datasets using xarray or rasterio/gdal."""
    name = 'raster-gdal'

    def register(self):
        "Register plugin by setting description and io type."
        self.description = 'IO for raster datasets using xarray or rasterio/gdal.'
        self.iotype = 'raster'

    def open(self, path, fmt, with_nodata=False, isel_band=None):
        "Open raster and return in requested format"

        if fmt is None or fmt.lower() == 'xarray':
            xarr = xr.open_rasterio(path, parse_coordinates=True)
            if isel_band is not None:
                xarr = xarr.isel(band=0)
            if with_nodata:
                xarr = convert_nodata_to_nans(xarr)
            return xarr

        raster_data = self.read(path)
        if fmt.lower() == 'rasterio':
            return raster_data

        if fmt.lower() == 'array':
            return raster_data.read()

        raise NotImplementedError('format %s not recognized' % fmt)

    def read(self, path):
        "Read raster using rasterio"
        return rasterio.open(path)

    def write(self, file_path, raster, metadata):
        "Write raster and metadata"
        raise NotImplementedError

    def visualize(self, path, reproject=False, crs=None):
        """Visualize raster dataset."""
        import rasterio

        base, ext = os.path.splitext(path)

        if reproject:
            reproject_dst = base + '-reproject' + ext
            if not crs:
                raise ValueError('MUST specify a destination coordinate system')
            with rasterio.open(path) as src:
                # write out tif file
                subprocess.check_output(['gdalwarp', path, reproject_dst, '-s_srs', src.crs.to_string(), '-t_srs', crs])
            base, ext = os.path.splitext(reproject_dst)
            path = reproject_dst

        dst = base + '.jpg'
        try:

            subprocess.check_output(['gdal_translate', '-expand', 'rgb', '-of','JPEG', path, dst])
        except Exception as e:
            try:
                 subprocess.check_output(['gdal_translate', '-of', 'JPEG', path, dst])
            except Exception as e:
                raise

        visualization_path = dst

        return  visualization_path

    def visualize_options(self, path, fmt='json'):
        """visualation options for raster datasets."""
        schema = {}
        return schema
