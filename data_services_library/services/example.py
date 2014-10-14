"""
Example Services
"""

from data_services_library.services import base
from geojson import Feature, FeatureCollection, Point, Polygon
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

        points = []
        for location in locations:
            properties = {'parameter': 'Temperature', 'units': 'degF', 'site_code': int(random()*1000000)}
            points.append(Feature(geometry=Point(location), properties=properties))

        return FeatureCollection(points)


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
            properties = {'parameter': 'LandCover', 'covertype': 'foilage', 'area_number': int(random()*10000)}
            triangle = [_random_point(bbox) for i in range(3)]
            triangle.append(triangle[0])
            triangles.append(Feature(geometry=Polygon([triangle]),
                properties=properties))

        return FeatureCollection(triangles)


def _random_point(bounding_box):
    x1, y1, x2, y2 = bounding_box

    return x1 + random()*(x2-x1), y1 + random()*(y2-y1)
