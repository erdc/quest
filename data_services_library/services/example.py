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
                    'bbox': [-128., 24., -64., 52.],
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
                    'bbox': [-128., 24., -64., 52.],
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


class ExampleVITD(base.DataServiceBase):
    def register(self):
        """Register Example points service 
        """
        self.metadata = {
                    'service_name': 'National Example Organization (NEO)',
                    'dataset_name': 'example vitd service',
                    'description': 'Terrain data values, vector data',
                    'geographical area': 'IRAQ',
                    'bbox': [35., 30., 50., 40.],
                    'geotype': 'polygons',
                    'type': 'vector'  #NEED TO FIGURE OUT HOW TO CLASSIFY DATA
                }

    def get_locations(self, bbox=None):
        rectangles = []
        id = 0
        for jj in range(4):
          yy = 34.0 + 0.5*jj
          for ii in range(8):
            xx = 41.15 + 0.5*ii
            p1 = (xx, yy)
            p2 = (xx + 0.5, yy)
            p3 = (xx + 0.5, yy + 0.5)
            p4 = (xx, yy + 0.5)
            rectangle = [p1, p2, p3, p4]
            properties = {'parameter': 'VITD data', 'area_number': id}
            rectangle.append(rectangle[0])
            rectangles.append(Feature(geometry=Polygon([rectangle]),
              properties=properties))
            id = id + 1

        # Add a few more rectangles that overlap
        p1 = (43., 35.2)
        p2 = (43.75, 35.2)
        p3 = (43.75, 35.8)
        p4 = (43., 35.8)
        rectangle = [p1, p2, p3, p4, p1]
        properties = {'parameter': 'VITD data', 'area_number': id}
        rectangles.append(Feature(geometry=Polygon([rectangle]),
          properties=properties))
        id = id + 1

        p1 = (43.75, 35.2)
        p2 = (44.5, 35.2)
        p3 = (44.5, 35.8)
        p4 = (43.75, 35.8)
        rectangle = [p1, p2, p3, p4, p1]
        properties = {'parameter': 'VITD data', 'area_number': id}
        rectangles.append(Feature(geometry=Polygon([rectangle]),
          properties=properties))
        id = id + 1

        return FeatureCollection(rectangles)
