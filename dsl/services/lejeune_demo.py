"""
Lejeune demo data
"""

from .. import util
from .base import DataServiceBase
from geojson import load
from zipfile import ZipFile
import os, shutil, string

DEFAULT_FILE_PATH_GHCN = 'ghcn'

class LejeuneGhcn(DataServiceBase):
    def register(self):
        """Register Lejeune PRCP service, 

        """
        self.demo_dir = util.get_dsl_demo_dir()
        self.metadata = {
                    'provider': {
                        'abbr': 'NCDC',
                        'name': 'Global Historic Climate Network', 
                        },
                    'display_name': 'GHCN Precipitation',
                    'service': 'NCDC GHCN Precipitation',
                    'description': 'NCDC GHCN Precipitation',
                    'geographical area': 'North Carolina',
                    'bounding_boxes': [[-84.321732, 33.840149, -75.460449, 36.588322]],
                    'geotype': 'points',
                    'datatype': 'timeseries'
                }


    def get_locations(self, locations=None, bounding_box=None):
        if locations:
            return self.get_feature_locations(locations)

        path = os.path.join(self.demo_dir, 'lejeune', 'ghcn_daily/stations.json')

        with open(path) as f:
            fc = load(f)

        return fc

    def get_feature_locations(self, features):
        if not isinstance(features, list):
            features = [features]
        locations = self.get_locations()
        locations['features'] = [feature for feature in locations['features'] if feature['id'] in features]
       
        return locations

    def get_data(self, locations, parameters=None, path=None):
        """parameter ignored, always equal to terrain-vitd
        """
        parameters = 'precipitation'

        if isinstance(locations, basestring):
            locations = [loc.strip() for loc in locations.split(',')]

        if not path:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH_GHCN)
        util.mkdir_if_doesnt_exist(path)

        #fake download
        zip_path = os.path.join(self.demo_dir, 'lejeune', 'ghcn_daily', 'precip.zip')    

        data_files = {}
        for location in locations:
            data_files[location] = {}
            fname = location + '_prcp.csv'
            with ZipFile(zip_path) as myzip:
                src = myzip.open(location + '_prcp.csv')
                dest = file(os.path.join(path, fname), "wb")
                print 'downloading file for %s from NCDC' % location
                with src, dest:
                    shutil.copyfileobj(src, dest)
            data_files[location][parameters] = os.path.join(path, fname)

        return data_files

    def get_locations_options(self):
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

    def get_data_options(self, **kwargs):
        schema = None
        return schema

    def provides(self):
        return ['precipitation']


