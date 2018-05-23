"""Timeseries Filters

DEPRECIATED .... NOT CURRENTLY WORKING WITH NEW API

"""
from __future__ import print_function

from quest.plugins import FilterBase
import os
from quest.util.log import logger


class ExportRaster(FilterBase):

    def register(self):
        """Register Timeseries

        """
        self.schema = {}

        self.metadata = {
            'group': 'Raster',
            'operates_on': {
                'datatype': ['Raster'],
                'geotype': ['Polygon'],
                'parameters': None,
            },
            'produces': None,
        }

    def apply_filter(self, collection_name, service, location, parameter, export_path, filename, fmt='USGSDEM'):

        collection = get_collection(collection_name)
        path = collection['path']
        dataset = collection['datasets'][service]['data']
        datafile = os.path.join(path, dataset[location][parameter]['relative_path'])
        datatype = dataset[location][parameter]['datatype']
        export_path = os.path.join(export_path, filename)

        if not datatype=='raster':
            logger.error('Cannot apply this plugin to not timeseries data')

            return

        try:
            import rasterio
            with rasterio.drivers():
                rasterio.copy(datafile, export_path, driver=fmt)

            logger.info('File exported to %s' % export_path)
        except:
            logger.errror('export failed')

        return collection

    def get_filter_options(self, **kwargs):
        properties = {
            "export_path": {
                "type": "string",
                "description": "adh export path",
            },
            "filename": {
                "type": "string",
                "description": "filename (without the .csv)",
            },
            "fmt": {
                "type": { "enum": [ 'USGSDEM', 'GTIFF', 'PNG', 'JPG'], "default": 'USGSDEM' },
                "description": "Simulation start time, if none given first value in dataset will be used",
            }
        }

        schema = {
            "title": "Export Raster",
            "type": "object",
            "properties": properties,
            "required": ['export_path', 'filename'],
        }

        return schema
