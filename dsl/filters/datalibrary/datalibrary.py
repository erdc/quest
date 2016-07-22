from .dl_base import DatalibraryBase
import os

class Vitd2Nrmm(DatalibraryBase):
    def register(self, name=None):
        """Register Timeseries

        """
        self.name = name
        self.template = 'vitd2nrmm.txt'
        self.metadata = {
            'group': 'vitd',
            'operates_on': {
                'datatype': 'vitd',
                'geotype': 'Polygon',
                'parameters': 'vitd',
            },
            'produces': {
                'datatype': 'nrmm',
                'geotype': 'Polygon',
                'parameters': 'nrmm',
            },
        }

    def apply_filter_options(self, fmt):
        return {}

    def _new_dataset_metadata(self):
        return {
            'parameter': 'nrmm',
            'datatype': 'nrmm',
            'file_format': 'nrmm',
        }


class Vitd2RasterVeg(DatalibraryBase):
    def register(self, name=None):
        """Register Timeseries

        """
        self.name = name
        self.template = 'vitd2raster-veg.txt'
        self.metadata = {
            'group': 'vitd',
            'operates_on': {
                'datatype': 'vitd',
                'geotype': 'Polygon',
                'parameters': 'vitd',
            },
            'produces': {
                'datatype': 'raster',
                'geotype': 'Polygon',
                'parameters': 'vegetation',
            },
        }

    def apply_filter_options(self, fmt):
        return {}

    def _new_dataset_metadata(self):

        self.save_path = os.path.join(self.save_path, 'vegetation.tiff')
        return {
            'parameter': 'vegetation',
            'datatype': 'raster',
            'file_format': 'gdal-raster',
        }
