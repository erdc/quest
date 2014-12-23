"""
Example Services
"""

from data_services_library.services import base
from ulmo.usgs import ned
from geojson import Feature, FeatureCollection, Point, Polygon, dump
import os


class UsgsNedBase(base.DataServiceBase):
    def set_layer(self, layer_name, layer_code):
        """Register USGS NED service 
        """

        self.layer = layer_name

        self.metadata = {
                    'provider': {'name': 'USGS', 'id': 'usgs-ned-' + layer_code},
                    'dataset_name': 'USGS National Elevation Dataset ' + layer_name,
                    'description': 'USGS National Elevation Dataset ' + layer_name,
                    'geographical area': '???',
                    'bbox': [-180, -90, 180, 90],
                    'geotype': 'polygons',
                    'type': 'raster'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        xmin, ymin, xmax, ymax = bbox

        return ned.get_raster_availability(self.layer, xmin, ymin, xmax, ymax)
        

class UsgsNed1ArcSecond(UsgsNedBase):
    def register(self):
        self.set_layer('1 arc-second', '1')


class UsgsNed13ArcSecond(UsgsNedBase):
    def register(self):
        self.set_layer('1/3 arc-second', '13')


class UsgsNed19ArcSecond(UsgsNedBase):
    def register(self):
        self.set_layer('1/9 arc-second', '19')


class UsgsNed2ArcSecond(UsgsNedBase):
    def register(self):
        self.set_layer('Alaska 2 arc-second', '2')


