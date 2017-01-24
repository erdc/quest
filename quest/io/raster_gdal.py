"""io plugin for timeseries datasets."""

from .base import IoBase
import os


class RasterGdal(IoBase):
    """IO for raster datasets using rasterio/gdal."""

    def register(self):
        "Register plugin by setting description and io type."
        self.description = 'IO for raster datasets using rasterio/gdal.'
        self.iotype = 'raster'

    def open(self, path, fmt):
        "Open raster and return in requested format"
        raise NotImplementedError

    def read(self, path):
        "Read raster using rasterio"
        raise NotImplementedError

    def write(self, file_path, raster, metadata):
        "Write raster and metadata"
        raise NotImplementedError

    def visualize(self, path, **kwargs):
        """Visualize raster dataset."""

        # TODO python visualization of raster datasets
        # For now raster datasets are just converted to geotiff and returned
        base, ext = os.path.splitext(path)
        if ext.lower() == 'tif' or ext.lower() == 'tiff':
            visualization_path = path
        else:
            visualization_path = base + '.tif'
            import rasterio
            with rasterio.drivers():
                rasterio.copy(path, visualization_path, driver='GTIFF')

        return visualization_path

    def visualize_options(self, path, fmt='json-schema'):
        """visualation options for raster datasets."""
        schema = {}
        return schema
