"""I/O plugin for Geojson with timeseries


"""
from .base import IoBase
from .. import util
from geojson import Feature, FeatureCollection, Point, Polygon, dump
from random import random
import os, shutil, string

DEFAULT_FILE_PATH = 'terrain-vitd'

class Vitd(IoBase):
    """Base class for I/O for different file formats
    """

    def register(self):
        """Register plugin by setting description and io type 
        """
        self.description = 'Reader/Writer for Geojson with timeseries in properties field'
        self.iotype = 'timeseries' 

    def read(self, path, as_dataframe=False):
        """Read data from format
        """
        with open(path) as f:
            data = json.load(f)

        if as_dataframe:
            data['values'] = pd.Series(data=data['values'], index=data['time'])
            del data['time']

        return data

    def write(self, path, location, name, longitude, latitude, parameter, unit, df, metadata=None):
        """Write data to format
        """

        feature = Feature(id=location,
                        geometry=Point((float(longitude),
                                        float(latitude))),
                        properties={
                            'name': name,
                            'parameter': parameter,
                            'metadata': metadata,
                            'unit_of_measurement': unit,
                            'time': df.index.to_native_types(),
                            'values': df.values.tolist(),
                        },
                    )
        if not path.endswith('.json'):
            path += '.json'

        base, fname = os.path.split(path)
        util.mkdir_if_doesnt_exist(base)

        with open(path, 'w') as f:
            dump(feature, f)

        print 'file written to: %s' % path

    def get_locations(self, locations=None, bounding_box=None, **kwargs):
        if locations is not None:
            return self.get_feature_locations(locations, **kwargs)

        src_path = kwargs.get('src_path')
        if src_path is None:
            raise IOError('src path not defined')

        path = os.path.join(src_path, 'mbr.txt')

        polys = []
        with open(path) as f:
            #skip first line which is a bunding polygon
            f.readline()
            for line in f:
                feature_id, x1, y1, x2, y2 = line.split()
                properties = {'feature_id': feature_id}
                polys.append(Feature(geometry=Polygon([_bbox2poly(x1, y1, x2, y2)]), properties=properties, id=feature_id))

        return FeatureCollection(polys)

    def get_feature_locations(self, features, **kwargs):
        if not isinstance(features, list):
            features = [features]
        locations = self.get_locations(**kwargs)
        locations['features'] = [feature for feature in locations['features'] if feature['id'] in features]
       
        return locations

    def get_locations_options(self, **kwargs):
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

    def get_data(self, locations, parameters=None, path=None, **kwargs):
        """parameter ignored, always equal to terrain-vitd
        """
        parameters = 'elevation'

        if isinstance(locations, basestring):
            locations = [loc.strip() for loc in locations.split(',')]

        src_path = kwargs.get('src_path')
        if not src_path:
            raise IOError('src path not defined')

        if not path:
            path = util.get_dsl_dir()

        path = os.path.join(path, DEFAULT_FILE_PATH)
        util.mkdir_if_doesnt_exist(path)

        #copy common files
        common_files = [f for f in os.listdir(src_path) if os.path.isfile(f)]
        for f in common_files:
            shutil.copy(f, path)

        #copy vitd data folder
        data_files = {}
        for location in locations:
            data_files[location] = {}
            fname = location
            src = os.path.join(src_path, fname)
            dest = os.path.join(path, fname)
            print 'downloading file for %s from NGA' % location
            shutil.copytree(src, dest)
            data_files[location][parameters] = dest

        return data_files

    def get_data_options(self, **kwargs):
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

    def provides(self, **kwargs):
        return ['elevation']


def _bbox2poly(x1, y1, x2, y2):
    xmin, xmax = sorted([float(x1), float(x2)])
    ymin, ymax = sorted([float(y1), float(y2)])
    poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
    poly.append(poly[0])

    return poly