"""Timeseries Filters

"""
from __future__ import print_function
import os

import param

from .ts_base import TsBase
from ...util import unit_registry, unit_list

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
    _name = 'ts-remove-outliers'
    sigma = param.Number(doc="values greater than (sigma * std deviation) from median will be filtered out")

    def register(self, name='ts-remove-outliers'):
        TsBase.register(self, name=name)

    def _apply(self, df):
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']
        parameter = metadata['parameter']
        sigma = self.sigma
        if sigma is None:
            sigma = 3

        # remove anything 'sigma' standard deviations from median
        vmin = df[parameter].median() - float(sigma)*df[parameter].std()
        vmax = df[parameter].median() + float(sigma)*df[parameter].std()
        df = df[(df[parameter] > vmin)]
        df = df[(df[parameter] < vmax)]
        df.metadata = metadata


        #if despike:
        #    kw = dict(n1=2, n2=20, block=6)
        #    df = despike(df, **kw)
        #    new_df = df.resample(periods[period], how=method, kind='period')

        return df


class TsUnitConversion(TsBase):
    _name = 'ts-unit-conversion'
    to_units = param.ObjectSelector(default=None,
                                    doc="""Units of the resulting dataset.""",
                                    objects=unit_list()
                                    )

    def register(self, name='ts-unit-conversion'):
        TsBase.register(self, name=name)

    def _apply(self, df):
        if self.to_units is None:
            raise ValueError('To_units cannot be None')

        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']

        reg = unit_registry()
        from_units = metadata['unit']
        if '/' in from_units and '/' not in self.to_units:
            beg = from_units.find('/')
            end = len(from_units)
            default_time = from_units[beg:end]
            to_units = self.to_units + default_time
        else:
            to_units = self.to_units
        conversion = reg.convert(1, src=from_units, dst=to_units)
        df[df.columns[1]] = df[df.columns[1]] * conversion
        metadata.update({'unit': to_units})
        df.metadata = metadata

        return df


class TsResample(TsBase):
    _name = 'ts-resample'
    # name = param.String(default='ts-resample')
    period = param.ObjectSelector(doc="resample frequency",
                                  objects=['daily', 'weekly', 'monthly', 'annual'],
                                  default='daily',
                                  precedence=1,
                                  )
    method = param.ObjectSelector(doc="resample method",
                                  objects=['sum', 'mean', 'std', 'max', 'min', 'median'],
                                  default='mean',
                                  precedence=2,
                                  allow_None=False,
                                  )

    def register(self, name='ts-resample'):
        TsBase.register(self, name=name)

    def _apply(self, df):
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']
        param = metadata['parameter']
        period = self.period
        method = self.method

        orig_param, orig_period, orig_method = (param.split(':') + [None, None])[:3]
        new_df = getattr(df.resample(periods[period], kind='period'), method)()

        new_param = '%s:%s:%s' % (orig_param, period, method)
        new_df.rename(columns={param: new_param}, inplace=True)  #inplace must be set to True to make changes

        metadata.update({'parameter': new_param})
        new_df.metadata = metadata
        return new_df


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
#     def _apply_filter(self, collection_name, service, location, parameter, export_path, filename, start_time=None):
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
