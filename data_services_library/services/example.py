"""
Example Services
"""

from data_services_library.services import base
#from geojson import Point
from random import random


class ExamplePoints(base.DataServiceBase):
    def register(self):
        """Register Example points service 
        """
        self.metadata = {
                    'service_name': 'National Example Organization (NEO)',
                    'dataset_name': 'example points service',
                    'description': 'Instantaneous values at monitoring locations',
                    'geographical area': 'CONUS',
                    'bbox': [24., -128., 52., -64.],
                    'geotype': 'points',
                    'type': 'timeseries' 
                }


    def get_locations(self, bbox=None):
        #get 100 random locations
        if not bbox:
            bbox = self.metadata['bbox']

        x1, y1, x2, y2 = bbox
        locations = [_random_point(bbox) for i in range(100)]



        return locations


class ExamplePolys(base.DataServiceBase):
    def register(self):
        """Register Example points service 
        """
        self.metadata = {
                    'service_name': 'National Example Organization (NEO)',
                    'dataset_name': 'example polys service',
                    'description': 'Instantaneous values at monitoring locations',
                    'geographical area': 'CONUS',
                    'bbox': [24., -128., 52., -64.],
                    'geotype': 'polygons',
                    'type': 'timeseries' 
                }


    def get_locations(self, bbox=None):
        #get 10 random triangle
        if not bbox:
            bbox = self.metadata['bbox']

        x1, y1, x2, y2 = bbox
        triangles = []
        for _ in range(10):
            triangles.append([_random_point(bbox) for i in range(3)])

        return triangles


def _random_point(bounding_box):
    x1, y1, x2, y2 = bounding_box

    return x1 + random()*(x2-x1), y1 + random()*(y2-y1)