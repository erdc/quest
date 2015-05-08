"""Plugin to create service from data in local/network folder

"""

from .. import util
from .base import DataServiceBase
#import fiona
from geojson import Feature, FeatureCollection, Point, Polygon, dump
from random import random
import os
import yaml


class LocalService(DataServiceBase):
    def __init__(self, path):
        self.register(path)

    def register(self, path):
        """Register local dataset 
        """

        config_file = os.path.join(path, 'dsl.yml')
        c = yaml.load(open(config_file, 'r'))
        self.metadata = c['metadata']
        self.format = c['format']['plugin']
        self.format_options = c['format']['options']
        if self.format_options is None:
            self.format_options = {}
        self.format_options['src_path'] = path
        self.name = c['name']
        self.io = util.load_drivers('io', self.format)[self.format].driver
        
    def get_locations(self, locations=None, bounding_box=None, **kwargs):
        kwargs.update(self.format_options)
        return self.io.get_locations(locations, bounding_box, **kwargs)

    def get_data(self, locations, parameters=None, **kwargs):
        kwargs.update(self.format_options)
        return self.io.get_data(locations, parameters, **kwargs)

    def get_locations_options(self, **kwargs):
        kwargs.update(self.format_options)
        return self.io.get_location_options(**kwargs)

    def get_data_options(self, **kwargs):
        kwargs.update(self.format_options)
        return self.io.get_data_options(**kwargs)

    def provides(self, **kwargs):
        kwargs.update(self.format_options)
        return self.io.provides(**kwargs)