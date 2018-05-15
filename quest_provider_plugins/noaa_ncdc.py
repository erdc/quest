"""QUEST wrapper for NCDC GHCN and GSOD Services."""
import os

import pandas as pd
import param
from ulmo.ncdc import ghcn_daily, gsod

from quest.plugins import ProviderBase, TimePeriodServiceBase
from quest import util
# from ulmo.ncdc.ghcn_daily.core import _get_inventory as _get_ghcn_inventory

BASE_PATH = 'ncdc'


class NcdcServiceBase(TimePeriodServiceBase):

    @property
    def metadata(self):
        return {
            'display_name': self.display_name,
            'description': self.description,
            'service_type': self.service_type,
            'parameters': list(self._parameter_map.values()),
            'unmapped_parameters_available': self.unmapped_parameters_available,
            'geom_type': self.geom_type,
            'datatype': self.datatype,
            'geographical_areas': self.geographical_areas,
            'bounding_boxes': self.bounding_boxes
        }
    
    @property
    def parameters(self):
        return {
            'parameters': list(self._parameter_map.values()),
            'parameter_codes': list(self._parameter_map.keys())
        }

    @property
    def parameter_code(self):
        pmap = self.parameter_map(invert=True)
        return pmap[self.parameter]

    def get_features(self):
        features = self._get_features()

        # remove locations with invalid coordinates
        valid = pd.notnull(features.latitude) & pd.notnull(features.longitude)
        features = features[valid]
        features.rename(columns={
            'name': 'display_name',
            'longitude': 'longitude',
            'latitude': 'latitude'
        }, inplace=True)

        # drop columns that just duplicate information already in the service_id
        features.drop(labels=['id', 'network_id', 'WBAN', 'USAF'], axis=1, inplace=True, errors='ignore')

        return features

    @property
    def feature(self):
        return self._feature

    @property
    def data(self):
        raise NotImplementedError()

    def parameter_map(self, invert=False):
        pmap = self._parameter_map

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def download(self, feature, file_path, dataset, **kwargs):
        p = param.ParamOverrides(self, kwargs)
        self.parameter = p.parameter
        self.end = pd.to_datetime(p.end)
        self.start = pd.to_datetime(p.start)
        self._feature = feature

        if dataset is None:
            dataset = 'station-' + feature

        # if end is None:
        #     end = pd.datetime.now().strftime('%Y-%m-%d')
        #
        # if start is None:
        #     start = pd.to_datetime(end) - pd.datetools.timedelta(days=30)
        #     start = start.strftime('%Y-%m-%d')

        file_path = os.path.join(file_path, BASE_PATH, self.service_name, dataset, '{0}.h5'.format(dataset))

        metadata = {
            'file_path': file_path,
            'file_format': 'timeseries-hdf5',
            'datatype': 'timeseries',
            'parameter': self.parameter,
            'unit': self._unit_map[self.parameter],
            'service_id': 'svc://ncdc:{}/{}'.format(self.service_name, feature)
        }

        # save data to disk
        io = util.load_entities('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        io.write(file_path, self.data, metadata)
        del metadata['service_id']

        return metadata


class NcdcServiceGhcnDaily(NcdcServiceBase):
    service_name = 'ghcn-daily'
    display_name = 'NCDC GHCN Daily'
    description = 'Daily Meteorologic Data from the Global Historic Climate Network'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90],
    ]
    _parameter_map = {
        'PRCP': 'rainfall:daily:total',
        'SNOW': 'snowfall:daily:total',
        'SNWD': 'snow_depth:daily:total',
        'TMAX': 'air_temperature:daily:total',
        'TMIN': 'air_temperature:daily:minimum',
        'TAVG': 'air_temperature:daily:mean'
    }
    _unit_map = {
        'rainfall:daily:total': '0.1*mm',
        'snowfall:daily:total': 'mm',
        'snow_depth:daily:total': 'mm',
        'air_temperature:daily:total': '0.1*degC',
        'air_temperature:daily:minimum': '0.1*degC',
        'air_temperature:daily:mean': '0.1*degC',
    }

    parameter = param.ObjectSelector(default=None, doc='parameter', precedence=1, objects=sorted(_parameter_map.values()))

    @property
    def data(self):
        data = ghcn_daily.get_data(self.feature,
                                   elements=self.parameter_code,
                                   as_dataframe=True)  # [parameter_code]
        if not data or data[self.parameter_code].empty:
            raise ValueError('No Data Available')

        data = data[self.parameter_code]

        data = data[self.start_string:self.end_string]
        if data.empty:
            raise ValueError('No Data Available')
        data.rename(columns={'value': self.parameter}, inplace=True)

        return data

    def _get_features(self, **kwargs):
        return ghcn_daily.get_stations(as_dataframe=True)


class NcdcServiceGsod(NcdcServiceBase):
    service_name = 'gsod'
    display_name = 'NCDC GSOD'
    description = 'Daily Meteorologic Data from the Global Summary of the Day'
    service_type = 'geo-discrete'
    unmapped_parameters_available = True
    geom_type = 'Point'
    datatype = 'timeseries'
    geographical_areas = ['Worldwide']
    bounding_boxes = [
        [-180, -90, 180, 90]
    ]
    _parameter_map = {
        'precip': 'rainfall:daily:total',
        'snow_depth': 'snow_depth:daily:total',
        'max_temp': 'air_temperature:daily:max',
        'min_temp': 'air_temperature:daily:min',
    }
    _unit_map = {
        'rainfall:daily:total': '0.01*inches',
        'snow_depth:daily:total': '0.01*inches',
        'air_temperature:daily:max': '0.1*degF',
        'air_temperature:daily:min': '0.1*degF',
        'air_temperature:daily:min': '0.1*degF',
    }
    parameter = param.ObjectSelector(default=None, doc='parameter', precedence=1, objects=sorted(_parameter_map.values()))

    @property
    def data(self):
        data = gsod.get_data(self.feature, start=self.start, end=self.end,
                             parameters=self.parameter_code)  # [feature]

        if not data or not data[self.feature]:
            raise ValueError('No Data Available')

        data = data[self.feature]
        data = pd.DataFrame(data)
        if data.empty:
            raise ValueError('No Data Available')

        data = data.set_index('date')
        data.index = pd.PeriodIndex(data.index, freq='D')
        data.rename(columns={self.parameter_code: self.parameter}, inplace=True)

        return data

    def _get_features(self, **kwargs):
        features = gsod.get_stations()
        features = pd.DataFrame.from_dict(features, orient='index')
        return features


class NcdcProvider(ProviderBase):
    service_base_class = NcdcServiceBase
    display_name = 'NCDC Web Services'
    description = 'Services available through the NCDC'
    organization_name = 'National Climatic Data Center'
    organization_abbr = 'NCDC'
    name = 'noaa-ncdc'
