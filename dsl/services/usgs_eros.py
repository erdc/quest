"""
Example Services
"""

from .base import DataServiceBase
from .. import util
from ulmo.usgs import eros
from geojson import FeatureCollection, dump
import json
import os

DEFAULT_FILE_PATH = 'usgs/eros'
CACHE_FILE = 'eros_%s_metadata.json'

class UsgsErosBase(DataServiceBase):
    def set_layer(self, product_key, layer_code, layer_name):
        """Register USGS EROS service 
        """

        self.product_key = product_key
        dsl_dir = util.get_dsl_dir()
        self.cache_file = os.path.join(dsl_dir, CACHE_FILE % layer_code)

        self.metadata = {
                    'provider': {
                        'abbr': 'USGS',
                        'name': 'United States Geological Survey', 
                        },
                    'display_name': 'USGS Landcover ' + layer_name,
                    'service': 'USGS Landcover ' + layer_name,
                    'description': 'USGS Landcover ' + layer_name,
                    'geographical area': 'CONUS',
                    'bounding_boxes': [[-124.848974, 24.396308, -66.885444, 49.384358]], #using conus for now
                    'geotype': 'polygons',
                    'datatype': 'raster'
                }

    def get_locations(self, locations=None, bounding_box=None):
        if locations:
            if isinstance(locations, basestring):
                locations = [loc.strip() for loc in locations.split(',')]

            with open(self.cache_file) as f:
                metadata = json.load(f)
                selected = [feature for feature in metadata['features'] if feature['id'] in locations]
                return FeatureCollection(selected)

        if not bounding_box:
            bounding_box = self.metadata['bounding_boxes'][0]

        if isinstance(bounding_box, basestring):
            bounding_box = [float(p) for p in bounding_box.split(',')]

        xmin, ymin, xmax, ymax = bounding_box

        locations = eros.get_raster_availability(self.product_key, xmin, ymin, xmax, ymax)

        if os.path.exists(self.cache_file):
            existing = json.load(open(self.cache_file))
            locations = util.append_features(existing, locations)

        with open(self.cache_file, 'w') as f:
            dump(locations, f)

        return locations

    def get_location_filters(self):
        schema = {
            "title": "Location Filters",
            "type": "object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "Optional single or comma delimited list of location identifiers",
                    },
                "bounding_box": {
                    "type": "string",
                    "description": "bounding box should be a comma delimited set of 4 numbers ",
                    },
            },
            "required": None,
        }
        return schema
        
    def get_data(self, locations, path=None, parameters=None):
        """parameter is always set to landcover
        """
        parameters = 'landcover'

        if not path:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH)
        locations = self.get_locations(locations=locations)
        tiles = eros.download_tiles(locations, path=path)
        return {tile['id']: {parameters: tile['properties']['file']} for tile in tiles['features']}

    def get_data_filters(self):
        schema = {
            "title": "Download Options",
            "type": "Object",
            "properties": {
                "locations": {
                    "type": "string",
                    "description": "single or comma delimited list of location identifiers to download data for",
                },
                "path": {
                    "type": "string",
                    "description": "base file path to store data"
                },
            },
            "required": ["locations"],
        }
        return schema

    def provides(self):
        return ['landcover']


class UsgsErosNlcd2001(UsgsErosBase):
    def register(self):
        self.set_layer('L1L', 'nlcd2006', 'NLCD 2006')
        

class UsgsErosNlcd2006(UsgsErosBase):
    def register(self):
        self.set_layer('L6N', 'nlcd2006', 'NLCD 2006')

