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
                    'bounding box': [24., -128., 52., -64.],
                    'geotype': 'points',
                    'type': 'timeseries' 
                }


    def get_locations(self, bounding_box=None):
        #get 100 random locations
        if not bounding_box:
            bounding_box = self.metadata['bounding_box']

        x1, y1, x2, y2 = bounding_box
        locations = [_random_point(bounding_box) for i in range(100)]



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
                    'bounding box': [24., -128., 52., -64.],
                    'geotype': 'polygons',
                    'type': 'timeseries' 
                }


    def get_locations(self, bounding_box=None):
        #get 10 random triangle
        if not bounding_box:
            bounding_box = self.metadata['bounding_box']

        x1, y1, x2, y2 = bounding_box
        triangles = []
        for _ in range(10):
            triangles.append([_random_point(bounding_box) for i in range(3)])

        return triangles


def _random_point(bounding_box):
    x1, y1, x2, y2 = bounding_box

    return x1 + random()*(x2-x1), y1 + random()*(y2-y1)