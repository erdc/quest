"""
Example Services
"""

from .base import SingleFileBase
from .. import util
from ulmo.usgs import ned
from ulmo.usgs.ned.core import _download_tiles as download_tiles
from geojson import FeatureCollection, dump
import json
import os

DEFAULT_FILE_PATH = os.path.join('usgs','ned')
CACHE_FILE = 'ned_%s_metadata.json'

class UsgsNedService(SingleFileBase):
    def _register(self):
        self.metadata = {
            'display_name': 'USGS National Elevation Dataset',
            'description': 'National Elevation Dataset at several resolutions',
            'organization': {
                'abbr': 'USGS',
                'name': 'United States Geological Survey', 
            },
        }

    def _layers(self):
        return {
            'alaska-2-arc-second': 'Alaska 2 arc-second',
            '1-arc-second': '1 arc-second', 
            '13-arc-second': '1/3 arc-second',
            '19-arc-second': '1/9 arc-second',
        }

    def _get_services(self):
        services ={}
        for service, description  in self._layers().iteritems():
            services[service] = { 
                'display_name': 'USGS National Elevation Dataset %s' % description,
                'description': 'Retrieve USGS NED at %s resolution' % description,
                'geographical_areas': ['Alaska', 'USA', 'Hawaii'],
                'parameters': ['elevation'],
                'unmapped_parameters_available': False,
                'bounding_boxes': [[-180, -90, 180, 90]],
                'geom_type': 'polygon',
                'datatype': 'raster',
            }

        return services

    def _get_features(self, service):
        service = self._layers()[service]
        features = util.to_dataframe(
            ned.get_raster_availability(service, (-180, -90, 180, 90))
        )
        features['parameters'] = 'elevation'
        features['file_format'] = 'raster'
        return features.rename(columns={'download url': 'download_url', 'format': 'extract_from_zip'})
        
    def _get_parameters(self, service, features=None):
        return {
            'parameters': ['elevation'],
            'parameter_codes': ['elevation'],
        }
