"""
Example Services
"""

from .. import util
from .base import DataServiceBase
import fiona
from geojson import Feature, FeatureCollection, Point, Polygon, dump
from random import random
import os, shutil, string

DEFAULT_FILE_PATH_VITD = 'agc/iraq/vitd'
DEFAULT_FILE_PATH_LIDAR = 'agc/iraq/lidar'

class IraqVITD(DataServiceBase):
    def register(self):
        """Register Iraq Demo VITD service 
        """
        self.demo_dir = util.get_dsl_demo_dir()
        self.metadata = {
                    'provider': {
                        'abbr': 'AGC',
                        'name': 'Army Geospatial Center', 
                        },
                    'display_name': 'Iraq Terrain Data - VITD',
                    'service': 'Iraq Terrain Data - VITD',
                    'description': 'Iraq VITD Dataset',
                    'geographical area': 'IRAQ',
                    'bounding_boxes': [[38.782, 28.833, 49.433, 37.358]],
                    'geotype': 'polygons',
                    'datatype': 'vitd'
                }


    def get_locations(self, locations=None, bounding_box=None):
        if locations:
            return self.get_feature_locations(locations)

        if not bounding_box:
            bounding_box = self.metadata['bounding_boxes'][0]

        path = os.path.join(self.demo_dir, 'iraq', 'iraq-vitd.txt')

        polys = []
        with open(path) as f:
            #skip first line which is a bunding polygon
            f.readline()
            for line in f:
                feature_id, x1, y1, x2, y2 = line.split()
                properties = {'feature_id': feature_id}
                polys.append(Feature(geometry=Polygon([_bbox2poly(x1, y1, x2, y2)]), properties=properties, id=feature_id))

        return FeatureCollection(polys)

    def get_feature_locations(self, features):
        if not isinstance(features, list):
            features = [features]
        locations = self.get_locations()
        locations['features'] = [feature for feature in locations['features'] if feature['id'] in features]
       
        return locations

    def get_data(self, locations, parameters=None, path=None):
        """parameter ignored, always equal to terrain-vitd
        """
        parameters = 'terrain-vitd'

        if isinstance(locations, basestring):
            locations = [loc.strip() for loc in locations.split(',')]

        if not path:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH_VITD)
        util.mkdir_if_doesnt_exist(path)

        #fake download
        src_path = os.path.join(self.demo_dir, 'iraq', 'srtm-vitd-bboxes')
        data_files = {}
        for location in locations:
            data_files[location] = {}
            fname = location + '.tif'
            src = os.path.join(src_path, fname)
            dest = os.path.join(path, fname)
            print 'downloading file for %s from agc' % location
            shutil.copy(src, dest)
            data_files[location][parameters] = dest

        return data_files

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

    def get_categories(self, filename):
        with open(filename) as f:
            s = filter(lambda x: x in string.printable, f.read())
        
        s = s.split(';')[-1]
        return {s[x:x+58][:3]:s[x:x+58][3:].strip() for x in range(0, len(s), 58)}

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
        return ['terrain-vitd']


class IraqAGCTLidar(DataServiceBase):
    def register(self):
        """Register Iraq Demo AGC Lidar service 
        """
        self.metadata = {
                    'provider': {
                        'abbr': 'AGC',
                        'name': 'Army Geospatial Center', 
                        },
                    'display_name': 'Iraq AGC T-Lidar',
                    'description': 'Iraq AGC T-Lidar Data',
                    'geographical area': 'IRAQ',
                    'bbox': [38.782, 28.833, 49.433, 37.358],
                    'geotype': 'polygons',
                    'type': 'lidar'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        demo_dir = util.get_dsl_demo_dir()
        path = os.path.join(demo_dir, 'iraq', 'TLIDAR_20101015_Index.shp')

        features = []
        with fiona.drivers():
            with fiona.open(path, 'r') as source:
                for feature in source:
                    features.append(feature)

        return FeatureCollection(features)

##########################################################################
# WARNING: AGC LIDAR CLASSES BELOW HAVE NOT BEEN REFACTORED TO NEW API YET 
##########################################################################
class IraqAGCALidar(DataServiceBase):
    def register(self):
        """Register Iraq Demo AGC Lidar service 
        """
        self.metadata = {
                    'provider': {'name': 'Army Geospatial Center (AGC)', 'id': 'agc'},
                    'dataset_name': 'Iraq AGC A-Lidar',
                    'description': 'Iraq AGC A-Lidar Data',
                    'geographical area': 'IRAQ',
                    'bbox': [38.782, 28.833, 49.433, 37.358],
                    'geotype': 'polygons',
                    'type': 'lidar'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        demo_dir = util.get_dsl_demo_dir()
        path = os.path.join(demo_dir, 'iraq', 'ALIDAR_20101015_Index.shp')

        features = []
        with fiona.drivers():
            with fiona.open(path, 'r') as source:
                for feature in source:
                    features.append(feature)

        return FeatureCollection(features)

def _bbox2poly(x1, y1, x2, y2):
    xmin, xmax = sorted([float(x1), float(x2)])
    ymin, ymax = sorted([float(y1), float(y2)])
    poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
    poly.append(poly[0])

    return poly