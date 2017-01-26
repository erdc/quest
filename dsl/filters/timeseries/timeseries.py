"""Timeseries Filters

"""
from __future__ import print_function

from .ts_base import TsBase
from dsl import util
from ...api.metadata import get_metadata
import pandas as pd
import numpy as np
import numpy.ma as ma
import os
from pint import UnitRegistry

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


class TsRemoveOutliers(TsBase):
    def register(self, name='ts-remove-outliers'):
        TsBase.register(self, name=name)

    def _apply(self, df, options):
        metadata = df.metadata
        if 'save_path' in metadata:
            del metadata['save_path']
        param = metadata['parameter']
        sigma = options.get('sigma')
        if sigma is None:
            sigma = 3

        # remove anything 'sigma' standard deviations from median
        vmin = df[param].median() - float(sigma)*df[param].std()
        vmax = df[param].median() + float(sigma)*df[param].std()
        df = df[(df[param] > vmin)]
        df = df[(df[param] < vmax)]
        df.metadata = metadata


        #if despike:
        #    kw = dict(n1=2, n2=20, block=6)
        #    df = despike(df, **kw)
        #    new_df = df.resample(periods[period], how=method, kind='period')

        return df

    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'smtk':
            schema = util.build_smtk('filter_options','filter_timeseries_remove_outliers.sbt')

        if fmt == 'json-schema':
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

class TsUnitConversion(TsBase):
    def register(self, name='ts-unit-conversion'):
        TsBase.register(self, name=name)

    def _apply(self, df, options):
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']

        path = "/Users/rditllkw/DSL/data-services-library/dsl/filters/timeseries/default_units.txt"
        reg = UnitRegistry(path)
        from_units = metadata['unit']
        if '/' in from_units and '/' not in options.get('to_units'):
            beg = from_units.find('/')
            end = len(from_units)
            default_time = from_units[beg:end]
            to_units = options.get('to_units') + default_time
        else:
            to_units = options.get('to_units')
        conversion = reg.convert(1, src=from_units, dst=to_units)
        df[df.columns[1]] = df[df.columns[1]] * conversion
        metadata.update({'units': to_units})
        df.metadata = metadata

        return df

    def apply_filter_options(self, fmt, **kwargs):
        # if fmt == 'smtk':
        #     schema = util.build_smtk('filter_options','filter_timeseries_remove_outliers.sbt')

        if fmt == 'json-schema':
            properties = {
                "to_units": {
                    "type": "string",
                    "description": "the unit to convert to ",
                },
            }

            schema = {
                "title": "Conversion Timeseries Filter",
                "type": "object",
                "properties": properties,
                "required":["to_units"],
            }

        return schema


class TsResample(TsBase):
    def register(self, name='ts-resample'):
        TsBase.register(self, name=name)

    def _apply(self, df, options):
        metadata = df.metadata
        if 'save_path' in metadata:
            del metadata['save_path']
        param = metadata['parameter']
        period = options.get('period')
        method = options.get('method')

        orig_param, orig_period, orig_method = (param.split(':') + [None, None])[:3]
        new_df = df.resample(periods[period], how=method, kind='period')

        new_param = '%s:%s:%s' % (orig_param, period, method)
        new_df.rename(columns={param: new_param},inplace=True)  #inplace must be set to True to make changes

        metadata.update({'parameter': new_param})
        new_df.metadata = metadata
        return new_df


    def apply_filter_options(self, fmt, **kwargs):
        if fmt == 'smtk':
            schema = util.build_smtk('filter_options','filter_timeseries_resample.sbt')

        if fmt == 'json-schema':
            properties = {
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


# class ToAdh(TsBase):
#     def register(self,name='ts-adh'):
#         """Register Timeseries
#
#         """
#         self.schema = {}
#
#         self.metadata = {
#             'operates_on': {
#                 'datatype': ['timeseries'],
#                 'geotype': ['polygon', 'point', 'line'],
#                 'parameters': ['streamflow'],
#                 'level': ['parameter']
#             },
#             'produces': None,
#
#         }
#
#         TsBase.register(self, name=name)
#
#     def apply_filter(self, collection_name, service, location, parameter, export_path, filename, start_time=None):
#
#         collection = get_collection(collection_name)
#         path = collection['path']
#         dataset = collection['datasets'][service]['data']
#         datafile = os.path.join(path, dataset[location][parameter]['relative_path'])
#         datatype = dataset[location][parameter]['datatype']
#
#         if not datatype=='timeseries':
#             print('Cannot apply this plugin to not timeseries data')
#             return
#
#         # hard coding to work only with ts_geojson for now
#         io = util.load_drivers('io', 'ts-geojson')['ts-geojson'].driver
#         df = io.read(datafile)
#
#         if start_time:
#             df = df[start_time:]
#
#         df['datetime'] = df.index
#         df.index = (df.index - df.index[0]).seconds
#         path = os.path.join(export_path, filename)
#         df.to_csv(path, index_label='seconds_from_starttime')
#         print('File exported to %s' % path)
#
#         return collection
#
#
#     def apply_filter_options(self, **kwargs):
#         properties = {
#             # "collection_name": {
#             #     "type": "string",
#             #     "description": "Name of collection",
#             # },
#             # "service": {
#             #     "type": "string",
#             #     "description": "Name of service",
#             # },
#             # "location": {
#             #     "type": "string",
#             #     "description": "Name of location",
#             # },
#             # "parameter": {
#             #     "type": "string",
#             #     "description": "Name of parameter",
#             # },
#             "export_path": {
#                 "type": "string",
#                 "description": "adh export path",
#             },
#             "filename": {
#                 "type": "string",
#                 "description": "filename (without the .csv)",
#             },
#             "start_time": {
#                 "type": "string",
#                 "description": "Simulation start time, if none given first value in dataset will be used",
#             }
#         }
#
#         schema = {
#             "title": "Timeseries to Adh Exporter",
#             "type": "object",
#             "properties": properties,
#             "required": ['export_path', 'filename'],
#         }
#
#         return schema
