"""
Example Services
"""

from .. import util
from data_services_library.services import base
import fiona
from geojson import Feature, FeatureCollection, Point, Polygon, dump
from random import random
import os


class IraqVITD(base.DataServiceBase):
    def register(self):
        """Register Iraq Demo VITD service 
        """
        self.metadata = {
                    'provider': {'name': 'Iraq VITD', 'id': 'iraq-vitd'},
                    'dataset_name': 'Iraq VITD',
                    'description': 'Iraq VITD Dataset',
                    'geographical area': 'IRAQ',
                    'bbox': [38.782, 28.833, 49.433, 37.358],
                    'geotype': 'polygons',
                    'type': 'vitd'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        demo_dir = util.get_dsl_demo_dir()
        path = os.path.join(demo_dir, 'iraq', 'iraq-vitd.txt')

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


    def download(self, **kwargs):

        if 'options' in kwargs:
            schema = { 
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "title": "Download Options",
            "properties": {
                "options": {
                    "type": "array",
                    "items": [
                        {
                            "name": "name",
                            "value": {
                                "type": "string",
                                "required": False,
                            }   
                        },
                        {
                            "name": "features",
                            "type": "array",
                            "minItems": 0,
                            "items": { "type": "string" },
                            "uniqueItems": False,
                            "required": False,
                        }
                        ]
                    }
                }
            }

            return schema

        features = self.get_locations()
        if 'features' in kwargs.keys():
            features['features'] = [feature for feature in features['features'] if feature['id'] in kwargs['features'][0].split(',')] 

        #add in filename uri's
        demo_dir = os.getenv('DSL_DEMO_DIR')
        path = os.path.join(demo_dir, 'iraq', 'srtm-vitd-bboxes')
        for feature in features['features']:
            feature['properties']['uri'] = 'file://' + os.path.join(path, feature['id'] + '.tif')


        dataset_name = kwargs.get('name')
        if dataset_name:
            dataset_name = dataset_name[0]
        else:
            dataset_name = 'iraq-vitd-' + str(hash(random()))

        #add feature to datasets file
        path = os.path.join(demo_dir, 'datasets', dataset_name + '.json')
        if not os.path.exists(os.path.join(demo_dir, 'datasets')):
            os.makedirs(os.path.join(demo_dir, 'datasets'))

        with open(path, 'a') as f:
            dump(features, f)

        js = {'success': True, 'dataset_uid': dataset_name}
        
        return js


class IraqAGCTLidar(base.DataServiceBase):
    def register(self):
        """Register Iraq Demo AGC Lidar service 
        """
        self.metadata = {
                    'provider': {'name': 'Army Geospatial Center (AGC)', 'id': 'agc'},
                    'dataset_name': 'Iraq AGC T-Lidar',
                    'description': 'Iraq AGC T-Lidar Data',
                    'geographical area': 'IRAQ',
                    'bbox': [38.782, 28.833, 49.433, 37.358],
                    'geotype': 'polygons',
                    'type': 'lidar'
                }


    def get_locations(self, bbox=None):
        if not bbox:
            bbox = self.metadata['bbox']

        demo_dir = os.getenv('DSL_DEMO_DIR')
        path = os.path.join(demo_dir, 'iraq', 'TLIDAR_20101015_Index.shp')

        features = []
        with fiona.drivers():
            with fiona.open(path, 'r') as source:
                for feature in source:
                    features.append(feature)

        return FeatureCollection(features)


class IraqAGCALidar(base.DataServiceBase):
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

        demo_dir = os.getenv('DSL_DEMO_DIR')
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