"""
Example Services
"""

from data_services_library.services import base
import fiona
from geojson import Feature, FeatureCollection, Point, Polygon
from random import random
import os
from .. import util

class ChesapeakeVTK(base.DataServiceBase):
    def register(self):
        """Register Chesapeake Demo VTK service 
        """
        self.metadata = {
                    'provider': {'name': 'Chesapeake Elevation', 'id': 'chesapeake-vtk'},
                    'dataset_name': 'Chesapeake Elevation',
                    'description': 'Chesapeake Elevation',
                    'geographical area': 'Chesapeake Bay',
                    'bbox': [-78., 36., -74., 41.],
                    'geotype': 'polygons',
                    'type': 'raster'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        demo_dir = util.get_dsl_demo_dir()
        path = os.path.join(demo_dir, 'chesapeake', 'test_chesapeake.vtk')
        x1, y1, x2, y2 = self.metadata['bbox']
        polys = []
        properties = {'uri': 'file://' + path}
        polys.append(Feature(geometry=Polygon([_bbox2poly(x1, y1, x2, y2)]), properties=properties, id='1'))

        return FeatureCollection(polys)


def _bbox2poly(x1, y1, x2, y2):
    xmin, xmax = sorted([float(x1), float(x2)])
    ymin, ymax = sorted([float(y1), float(y2)])
    poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
    poly.append(poly[0])

    return poly