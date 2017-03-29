"""
Example Services
"""

from .base import SingleFileBase
from .. import util
from ulmo.usgs import ned
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
        services = {}
        for service, description in self._layers().items():
            services[service] = {
                'display_name': 'USGS National Elevation Dataset %s' % description,
                'description': 'Retrieve USGS NED at %s resolution' % description,
                'service_type': 'geo-discrete',
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
        features = util.to_geodataframe(
            ned.get_raster_availability(service, (-180, -90, 180, 90))
        )
        if features.empty:
            return features

        features['parameters'] = 'elevation'
        #features['file_format'] = 'raster-gdal'
        features['filename'] = features['download url'].apply(lambda x: x.split('/')[-1])
        columns = {
            'name': 'display_name',
            'download url': 'download_url',
            'format': 'extract_from_zip',
            }
        features['reserved'] = features['download url'].apply(lambda x: {'download_url': x, 'file_format': 'raster-gdal','extract_from_zip': '.img'})
        return features.rename(columns=columns)

    def _get_parameters(self, service, features=None):
        return {
            'parameters': ['elevation'],
            'parameter_codes': ['elevation'],
        }
