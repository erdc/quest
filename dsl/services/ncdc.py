"""DSL wrapper for NCDC GHCN and GSOD Services."""
from .base import WebServiceBase
from .. import util
import pandas as pd
import os
from ulmo.ncdc import ghcn_daily, gsod
# from ulmo.ncdc.ghcn_daily.core import _get_inventory as _get_ghcn_inventory

BASE_PATH = 'ncdc'

class NcdcService(WebServiceBase):
    def _register(self):
        self.metadata = {
            'display_name': 'NCDC Web Services',
            'description': 'Services available through the NCDC',
            'organization': {
                'abbr': 'NCDC',
                'name': 'National Climatic Data Center',
            },
        }

    def _get_services(self):
        return {
            'ghcn-daily': {
                'display_name': 'NCDC GHCN Daily',
                'description': 'Daily Meteorologic Data from the Global '
                               'Historic Climate Network',
                'service_type': 'geo-discrete',
                'parameters': self._parameter_map('ghcn-daily').values(),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes': [
                    [-180, -90, 180, 90],
                ],
            },
            'gsod': {
                'display_name': 'NCDC GSOD',
                'description': 'Daily Meteorologic Data from the Global '
                               'Summary of the Day',
                'service_type': 'geo-discrete',
                'parameters': self._parameter_map('gsod').values(),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes': [
                    [-180, -90, 180, 90],
                ],
            },
        }

    def _get_features(self, service):
        if service == 'ghcn-daily':
            features = ghcn_daily.get_stations(as_dataframe=True)

        if service == 'gsod':
            features = gsod.get_stations()
            features = pd.DataFrame.from_dict(features, orient='index')
            # currently to_geojson can't handle datetime objects so deleting these for now.
            del features['begin']
            del features['end']
            # these fields are causing problems when saving to database
            features = features.drop(['USAF', 'WBAN'], axis=1)

        # remove locations with invalid coordinates
        valid = pd.notnull(features.latitude) & pd.notnull(features.longitude)
        features = features[valid]
        features.rename(columns={
                            'name': '_display_name',
                            'longitude': '_longitude',
                            'latitude': '_latitude'
                        }, inplace=True)
        features['_service_id'] = features.index
        features['_geom_type'] = 'Point'
        features['_geom_coords'] = \
            zip(features['_longitude'], features['_latitude'])
        return features

    def _get_parameters(self, service, features=None):
        if service=='ghcn-daily':
            # too slow for that large a dataframe
            #parameters = _get_ghcn_inventory()
            #parameters.rename(columns={'id': 'feature_id', 'element': 'parameter_code', 'first_year': 'begin_date', 'last_year': 'end_date'}, inplace=True)
            #parameters['parameter'] = parameters['parameter_code'].apply(lambda x: self._parameter_map(service).get(x))

            # hardcoding for now
            parameters = {
                '_parameters': self._parameter_map('ghcn-daily').values(),
                '_parameter_codes': self._parameter_map('ghcn-daily').keys()
            }

        if service=='gsod':
            # this is not the real list of parameters. hardcoding for now
            parameters = {
                '_parameters': self._parameter_map('gsod').values(),
                '_parameter_codes': self._parameter_map('gsod').keys()
            }

        return parameters

    def _parameter_map(self, service, invert=False):
        if service=='ghcn-daily':
            pmap = {
                'PRCP': 'rainfall:daily:total',
                'SNOW': 'snowfall:daily:total',
                'SNWD': 'snow_depth:daily:total',
                'TMAX': 'air_temperature:daily:total',
                'TMIN': 'air_temperature:daily:minimum',
                'TAVG': 'air_temperature:daily:mean',
            }

        if service=='gsod':
            pmap = {
                'precip': 'rainfall:daily:total',
                'snow_depth': 'snow_depth:daily:total',
                'max_temp': 'air_temperature:daily:max',
                'min_temp': 'air_temperature:daily:min',
                'max_temp': 'air_temperature:daily:min',
            }

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def _download(self, service, feature, save_path, dataset,
                  parameter, start=None, end=None):

        if end is None:
            end = pd.datetime.now().strftime('%Y-%m-%d')

        if start is None:
            start = pd.to_datetime(end) - pd.datetools.timedelta(days=30)
            start = start.strftime('%Y-%m-%d')

        pmap = self._parameter_map(service, invert=True)
        parameter_code = pmap[parameter]

        if service == 'ghcn-daily':
            data = ghcn_daily.get_data(feature,
                                       elements=parameter_code,
                                       as_dataframe=True)[parameter_code]
            if data.empty:
                raise ValueError('No Data Available')

            data = data[start:end]
            data.rename(columns={'value': parameter}, inplace=True)

        if service == 'gsod':
            data = gsod.get_data(feature, start=start, end=end,
                                 parameters=parameter_code)[feature]
            data = pd.DataFrame(data)
            if data.empty:
                raise ValueError('No Data Available')

            data = data.set_index('date')
            data.index = pd.PeriodIndex(data.index, freq='D')
            data.rename(columns={parameter_code: parameter}, inplace=True)

        save_path = os.path.join(save_path, BASE_PATH, service)
        save_path = os.path.join(save_path, dataset)
        metadata = {
            'save_path': save_path,
            'file_format': 'hdf5',
            'datatype': 'timeseries',
            'parameter': parameter,
            'units': self._unit_map(service)[parameter],
            'service_id': 'svc://ncdc:{}/{}'.format(service, feature)
        }

        # save data to disk
        io = util.load_drivers('io', 'timeseries-hdf5')
        io = io['timeseries-hdf5'].driver
        io.write(save_path, data, metadata)
        del metadata['service_id']

        return metadata

    def _download_options(self, service):
        schema = {
            "title": "NCDC Download Options",
            "type": "object",
            "properties": {
                "parameter": {
                    "type": "string",
                    "enum": self._parameter_map(service).values(),
                    "description": "parameter",
                },
                "start": {
                    "type": "string",
                    "description": "start date",
                },
                "end": {
                    "type": "string",
                    "description": "end date",
                },
            },
        }
        return schema

    def _unit_map(self, service):
        if service == 'ghcn-daily':
            umap = {
                'rainfall:daily:total': '0.1*mm',
                'snowfall:daily:total': 'mm',
                'snow_depth:daily:total': 'mm',
                'air_temperature:daily:total': '0.1*degC',
                'air_temperature:daily:minimum': '0.1*degC',
                'air_temperature:daily:mean': '0.1*degC',
            }

        if service == 'gsod':
            umap = {
                'rainfall:daily:total': '0.01*inches',
                'snow_depth:daily:total': '0.01*inches',
                'air_temperature:daily:max': '0.1*degF',
                'air_temperature:daily:min': '0.1*degF',
                'air_temperature:daily:min': '0.1*degF',
            }

        return umap
