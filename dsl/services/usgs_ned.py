"""
Example Services
"""

from .base import DataServiceBase
from .. import util
from ulmo.usgs import ned
from geojson import FeatureCollection, dump
import json
import os

DEFAULT_FILE_PATH = 'usgs/ned'
CACHE_FILE = 'ned_%s_metadata.json'

class UsgsNedBase(DataServiceBase):
    def set_layer(self, layer_name, layer_code):
        """Register USGS NED service 
        """

        self.layer = layer_name
        dsl_dir = util.get_dsl_dir()
        self.cache_file = os.path.join(dsl_dir, CACHE_FILE % layer_code)

        self.metadata = {
                    'provider': {
                        'abbr': 'USGS',
                        'name': 'United States Geological Survey', 
                        },
                    'display_name': 'USGS National Elevation Dataset ' + layer_name,
                    'service': 'USGS National Elevation Dataset ' + layer_name,
                    'description': 'NED elevations',
                    'bounding_boxes': [[-180, -90, 180, 90]],
                    'geotype': 'polygons',
                    'datatype': 'raster'
                }


    def get_locations(self, locations=None, bounding_box=None):
        if locations is not None:
            try:
                with open(self.cache_file) as f:
                    metadata = json.load(f)
            except:
                metadata = self.get_locations()

            selected = [feature for feature in metadata['features'] if feature['id'] in locations]
            return FeatureCollection(selected)

        if bounding_box is None:
            bounding_box = self.metadata['bounding_boxes'][0] 

        xmin, ymin, xmax, ymax = [float(p) for p in bounding_box]

        locations = ned.get_raster_availability(self.layer, xmin, ymin, xmax, ymax)

        if os.path.exists(self.cache_file):
            existing = json.load(open(self.cache_file))
            locations = util.append_features(existing, locations)

        with open(self.cache_file, 'w') as f:
            dump(locations, f)

        return locations

    def get_locations_filters(self):
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
        """parameter is always set to elevation
        """
        parameters = 'elevation'

        if not path:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH)
        locations = self.get_locations(locations=locations)
        tiles = ned.download_tiles(locations, path=path)
        return {tile['id']: {parameters: tile['properties']['file']} for tile in tiles['features']}

    def get_data_filters(self):
        schema = {
            "title": "Download Options",
            "type": "object",
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
        return ['elevation']


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


