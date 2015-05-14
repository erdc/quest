"""Timeseries Filters

"""

from .base import FilterBase
from ..api import get_collection, add_to_collection
from .. import util
from geojson import Polygon, Feature, FeatureCollection
import pandas as pd
import os


class TsResample(FilterBase):
    def register(self):
        """Register Timeseries

        """
        self.schema = {}

        self.metadata = {
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': None,
                'level': ['parameter']
            },
            'produces': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': None,
            },
        }


    def apply_filter(self, collection_name, service, location, parameter, period, method):
        
        collection = get_collection(name)
        path = collection['path']
        dataset = collection['datasets'][service]['data']
        datafile = os.path.join(path, dataset[location][parameter]['relative_path'])
        datatype = dataset[location][parameter]['datatype']

        if datatype is not 'timeseries':
            print 'Cannot apply this plugin to not timeseries data'
            return

        # hard coding to work only with ts_geojson for now
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver       
        df = io.read(datafile)
        metadata = df.metadata
        metadata.update({'derived_using': 'timeseries plugin'})
        feature = df.feature

        new_df = df.resample(period, how=method)
        cols = []
        for col in df.columns:
            cols.append('%s %s %s' % (col, period, method))
        new_df.columns = cols
        parameter = '%s %s %s' % (parameter, period, method)
        plugin_dir = os.path.join(collection['path'], 'derived_ts')
        util.mkdir_if_doesnt_exist(plugin_dir)
        #dest = 'nrmm/data-%s.dat' % nrmm_id
        ts_file = 'local:stn-%s-%s-%s.json' % (location, period, methos)
        io.write(filename, location_id=location, geometry=feature['geometry'], dataframe=new_df, metadata=metadata)
        properties = {'relative_path': ts_file, 'datatype': 'timeseries'}
        properties.update(metadata)
        new_locs = FeatureCollection([Feature(geometry=feature['geometry'], properties=properties, id=location)])
        collection = add_to_collection(collection_name, 'local', new_locs, parameters=parameter)

        return collection


    def apply_filter_options(self, **kwargs):
        properties = {
            "collection_name": {
                "type": "string",
                "description": "Name of collection",
            }, 
            "service": {
                "type": "string",
                "description": "Name of service",
            },
            "location": {
                "type": "string",
                "description": "Name of location",
            },
            "parameter": {
                "type": "string",
                "description": "Name of location",
            },
            "period": {
                "type": { "enum": [ 'D', 'M', 'A' ], "default": 'M' },
                "description": "resample frequency (D-Daily, M-Monthly, A-Annual",    
            },
            "method": {
                "type": { "enum": [ 'sum', 'mean', 'std', 'max', 'min', 'median'], "default": 'mean' },
                "description": "resample method",    
            }

        }

        schema = {
            "title": "Download Options",
            "type": "object",
            "properties": properties,
            "required": ["collection_name", "service", "location", 'parameter', 'period', 'method'],
        }
        
        return schema