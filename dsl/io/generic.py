"""Generic plugin for file based datasets

"""
from .base import IoBase
from .. import util
import fiona
from geojson import Feature, FeatureCollection, Point, Polygon, dump, load
from random import random
import os, shutil, string


class Generic(IoBase):
    """Base class for I/O for different file formats
    """

    def register(self):
        """Register plugin by setting description and io type 
        """
        self.description = 'Reader/Writer for Generic datasets as a collection of files'
        self.iotype = 'generic' 

    def read(self):
        """Read data from format
        """
        pass

    def write(self):
        """Write data to format
        """
        pass

    def get_locations(self, locations=None, bounding_box=None, **kwargs):
        if locations is not None:
            return self.get_feature_locations(locations, **kwargs)

        src_path = kwargs.get('src_path')
        if src_path is None:
            raise IOError('src path not defined')

        path = os.path.join(src_path, kwargs['location_file'])
        fmt = kwargs['location_fmt']

        if fmt.lower()=='geojson':
            return load(open(path))

        if fmt.lower()=='shapefile':
            features = []
            with fiona.drivers():
                with fiona.open(path, 'r') as source:
                    for feature in source:
                        features.append(feature)

            return FeatureCollection(features)

        if fmt.lower()=='txt-bbox':
            polys = []
            with open(path) as f:
                #skip first line which is a bunding polygon
                f.readline()
                for line in f:
                    feature_id, x1, y1, x2, y2 = line.split()
                    properties = {'feature_id': feature_id}
                    polys.append(Feature(geometry=Polygon([_bbox2poly(x1, y1, x2, y2)]), properties=properties, id=feature_id))

            return FeatureCollection(polys)

        raise IOError('Format not recognized: %s' % fmt)

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
        if parameters is None:
            parameters = self.provides(**kwargs)

        if isinstance(locations, basestring):
            locations = [loc.strip() for loc in locations.split(',')]

        src_path = kwargs.get('src_path')
        if not src_path:
            raise IOError('src path not defined')

        if not path:
            path = util.get_dsl_dir()

        save_folder = kwargs.get('save_folder')
        path = os.path.join(path, save_folder)
        util.mkdir_if_doesnt_exist(path)

        #copy vitd data folder
        mapping = kwargs['mapping']
        data_files = {}
        for location in locations:
            for parameter in parameters:
                data_files[location] = {}
                fname = mapping.replace('<location>', location)
                fname = fname.replace('<parameter>', parameter)
                src = os.path.join(src_path, fname)
                dest = os.path.join(path, fname)
                print src, dest
                print 'downloading file for %s, %s' % (location, parameter)
                shutil.copy(src, dest)
                data_files[location][parameter] = dest

        return data_files

    def get_data_options(self, **kwargs):
        schema = None
        return schema

    def provides(self, **kwargs):
        return kwargs['provides']


def _bbox2poly(x1, y1, x2, y2):
    xmin, xmax = sorted([float(x1), float(x2)])
    ymin, ymax = sorted([float(y1), float(y2)])
    poly = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
    poly.append(poly[0])

    return poly
