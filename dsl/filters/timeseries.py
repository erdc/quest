"""Timeseries Filters

"""
from __future__ import print_function

from .base import FilterBase
from ..api import get_collection, add_to_collection
from .. import util
from geojson import Polygon, Feature, FeatureCollection
import pandas as pd
import numpy as np
import numpy.ma as ma
import os

periods = {
    'daily': 'D',
    'weekly': 'W',
    'monthly': 'M',
    'annual': 'A',
}

## USE LATER FOR DESPIKE FILTER
# def rolling_window(data, block):
#     shape = data.shape[:-1] + (data.shape[-1] - block + 1, block)
#     strides = data.strides + (data.strides[-1],)
#     return np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)


# def despike(arr, n1=2, n2=20, block=10):
#     offset = arr.values.min()
#     arr -= offset
#     data = arr.copy()
#     roll = rolling_window(data.values, block)
#     roll = ma.masked_invalid(roll)
#     std = n1 * roll.std(axis=1)
#     mean = roll.mean(axis=1)
#     # Use the last value to fill-up.
#     std = np.r_[std, np.tile(std[-1], block - 1)]
#     mean = np.r_[mean, np.tile(mean[-1], block - 1)]
#     mask = (np.abs(data - mean.filled(fill_value=np.NaN)) >
#             std.filled(fill_value=np.NaN))
#     data[mask] = np.NaN
#     # Pass two: recompute the mean and std without the flagged values from pass
#     # one now removing the flagged data.
#     roll = rolling_window(data.values, block)
#     roll = ma.masked_invalid(roll)
#     std = n2 * roll.std(axis=1)
#     mean = roll.mean(axis=1)
#     # Use the last value to fill-up.
#     std = np.r_[std, np.tile(std[-1], block - 1)]
#     mean = np.r_[mean, np.tile(mean[-1], block - 1)]
#     mask = (np.abs(arr - mean.filled(fill_value=np.NaN)) >
#             std.filled(fill_value=np.NaN))
#     arr[mask] = np.NaN
#     return arr + offset


class TsRemoveOutliers(FilterBase):
    def register(self):
        """Register Timeseries

        """
        self.schema = {}

        self.metadata = {
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': ['streamflow'],
                'level': ['parameter']
            },
            'produces': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': None,
            },
        }

    def apply_filter(self, collection_name, service, location, parameter, sigma=3):
        
        collection = get_collection(collection_name)
        path = collection['path']
        dataset = collection['datasets'][service]['data']
        datafile = os.path.join(path, dataset[location][parameter]['relative_path'])
        datatype = dataset[location][parameter]['datatype']

        if not datatype=='timeseries':
            print('Cannot apply this plugin to not timeseries data')
            return

        # hard coding to work only with ts_geojson for now
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver       
        df = io.read(datafile)
        metadata = df.metadata
        metadata.update({'derived_using': 'ts-remove-outliers plugin'})
        feature = df.feature

        #remove anything 3 standard deviations from median
        vmin = df.median() - float(sigma)*df.std()
        vmax = df.median() + float(sigma)*df.std()
        df = df[(df > vmin)]
        df = df[(df < vmax)]

        #if despike:
        #    kw = dict(n1=2, n2=20, block=6)
        #    df = despike(df, **kw)
        #    new_df = df.resample(periods[period], how=method, kind='period')
        
        cols = []
        for col in df.columns:
            cols.append('%s (outliers removed)' % (col))
        
        df.columns = cols
        parameter = '%s (outliers removed)' % (parameter)
        plugin_dir = os.path.join(collection['path'], 'derived_ts')
        util.mkdir_if_doesnt_exist(plugin_dir)
        #dest = 'nrmm/data-%s.dat' % nrmm_id
        ts_file = 'local:stn-%s-%s.json' % (location, parameter)
        filename = os.path.join(plugin_dir, ts_file)
        io.write(filename, location_id=location, geometry=feature['geometry'], dataframe=df, metadata=metadata)
        properties = {'relative_path': filename, 'datatype': 'timeseries'}
        properties.update(metadata)
        new_locs = FeatureCollection([Feature(geometry=feature['geometry'], properties=properties, id=location)])
        collection = add_to_collection(collection_name, 'local', new_locs, parameters=parameter)

        return collection

    def apply_filter_options(self, **kwargs):
        properties = {
            "sigma": {
                "type": "number",
                "description": "values greater than (sigma * std deviation) from median will be filtered out",    
            },
        }

        schema = {
            "title": "Outlier Timeseries Filter",
            "type": "object",
            "properties": properties,
        }
        
        return schema


class TsResample(FilterBase):
    def register(self):
        """Register Timeseries

        """
        self.schema = {}

        self.metadata = {
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': ['streamflow'],
                'level': ['parameter']
            },
            'produces': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': None,
            },
        }


    def apply_filter(self, collection_name, service, location, parameter, period, method):
        
        collection = get_collection(collection_name)
        path = collection['path']
        dataset = collection['datasets'][service]['data']
        datafile = os.path.join(path, dataset[location][parameter]['relative_path'])
        datatype = dataset[location][parameter]['datatype']

        if not datatype=='timeseries':
            print('Cannot apply this plugin to not timeseries data')
            return

        # hard coding to work only with ts_geojson for now
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver       
        df = io.read(datafile)
        metadata = df.metadata
        metadata.update({'derived_using': 'ts-resample plugin'})
        feature = df.feature

        new_df = df.resample(periods[period], how=method, kind='period')
        cols = []
        for col in df.columns:
            cols.append('%s %s %s' % (col, period, method))
        new_df.columns = cols
        parameter = '%s %s %s' % (parameter, period, method)
        plugin_dir = os.path.join(collection['path'], 'derived_ts')
        util.mkdir_if_doesnt_exist(plugin_dir)
        ts_file = 'local:stn-%s-%s-%s-%s.json' % (location, parameter, period, method)
        filename = os.path.join(plugin_dir, ts_file)
        io.write(filename, location_id=location, geometry=feature['geometry'], dataframe=new_df, metadata=metadata)
        properties = {'relative_path': filename, 'datatype': 'timeseries'}
        properties.update(metadata)
        new_locs = FeatureCollection([Feature(geometry=feature['geometry'], properties=properties, id=location)])
        collection = add_to_collection(collection_name, 'local', new_locs, parameters=parameter)

        return collection


    def apply_filter_options(self, **kwargs):
        properties = {
            # "collection_name": {
            #     "type": "string",
            #     "description": "Name of collection",
            # }, 
            # "service": {
            #     "type": "string",
            #     "description": "Name of service",
            # },
            # "location": {
            #     "type": "string",
            #     "description": "Name of location",
            # },
            # "parameter": {
            #     "type": "string",
            #     "description": "Name of parameter",
            # },
            "period": {
                "type": { "enum": [ 'daily', 'weekly', 'monthly', 'annual' ], "default": 'daily' },
                "description": "resample frequency",    
            },
            "method": {
                "type": { "enum": [ 'sum', 'mean', 'std', 'max', 'min', 'median'], "default": 'mean' },
                "description": "resample method",    
            }

        }

        schema = {
            "title": "Resample Timeseries Filter",
            "type": "object",
            "properties": properties,
            "required": ['period', 'method'],
        }
        
        return schema


class ToAdh(FilterBase):
    def register(self):
        """Register Timeseries

        """
        self.schema = {}

        self.metadata = {
            'operates_on': {
                'datatype': ['timeseries'],
                'geotype': ['polygon', 'point', 'line'],
                'parameters': ['streamflow'],
                'level': ['parameter']
            },
            'produces': None,
        }


    def apply_filter(self, collection_name, service, location, parameter, export_path, filename, start_time=None):
        
        collection = get_collection(collection_name)
        path = collection['path']
        dataset = collection['datasets'][service]['data']
        datafile = os.path.join(path, dataset[location][parameter]['relative_path'])
        datatype = dataset[location][parameter]['datatype']

        if not datatype=='timeseries':
            print('Cannot apply this plugin to not timeseries data')
            return

        # hard coding to work only with ts_geojson for now
        io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver       
        df = io.read(datafile)

        if start_time:
            df = df[start_time:]

        df['datetime'] = df.index
        df.index = (df.index - df.index[0]).seconds
        path = os.path.join(export_path, filename)
        df.to_csv(path, index_label='seconds_from_starttime')
        print('File exported to %s' % path)

        return collection


    def apply_filter_options(self, **kwargs):
        properties = {
            # "collection_name": {
            #     "type": "string",
            #     "description": "Name of collection",
            # }, 
            # "service": {
            #     "type": "string",
            #     "description": "Name of service",
            # },
            # "location": {
            #     "type": "string",
            #     "description": "Name of location",
            # },
            # "parameter": {
            #     "type": "string",
            #     "description": "Name of parameter",
            # },
            "export_path": {
                "type": "string",
                "description": "adh export path",    
            },
            "filename": {
                "type": "string",
                "description": "filename (without the .csv)",    
            },
            "start_time": {
                "type": "string",
                "description": "Simulation start time, if none given first value in dataset will be used",    
            }
        }

        schema = {
            "title": "Timeseries to Adh Exporter",
            "type": "object",
            "properties": properties,
            "required": ['export_path', 'filename'],
        }
        
        return schema