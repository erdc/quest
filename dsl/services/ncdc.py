"""DSL wrapper for USGS NWIS Services

"""
from .base import WebServiceBase
import concurrent.futures
from functools import partial
import pandas as pd
import os
from ulmo.ncdc import ghcn_daily, gsod
from ulmo.ncdc.ghcn_daily.core import _get_inventory as _get_ghcn_inventory
from .. import util


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
                'description': 'Daily Meteorologic Data from the Global Historic Climate Netword',
                'parameters': self._parameter_map('ghcn-daily').values(),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes' : [
                    [-180, -90, 180, 90],
                ],
            },
            'gsod': {
                'display_name': 'NCDC GSOD',
                'description': 'Daily Meteorologic Data from the Global Summary of thr Day',
                'parameters': self._parameter_map('gsod').values(),
                'unmapped_parameters_available': True,
                'geom_type': 'Point',
                'datatype': 'timeseries',
                'geographical_areas': ['Worldwide'],
                'bounding_boxes' : [
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

        features[pd.notnull(features.latitude) & pd.notnull(features.longitude)]
        features['geom_type'] = 'Point'
        features['geom_coords'] = zip(features['longitude'], features['latitude'])
        return features

    def _get_parameters(self, service, features=None):
        if service=='ghcn-daily':
            # too slow for that large a dataframe
            #parameters = _get_ghcn_inventory()
            #parameters.rename(columns={'id': 'feature_id', 'element': 'parameter_code', 'first_year': 'begin_date', 'last_year': 'end_date'}, inplace=True)
            #parameters['parameter'] = parameters['parameter_code'].apply(lambda x: self._parameter_map(service).get(x))

            # hardcoding for now
            parameters = {
                'parameters': self._parameter_map('ghcn-daily').values(),
                'parameter_codes': self._parameter_map('ghcn-daily').keys()
            }

        if service=='gsod':
            # this is not the real list of parameters. hardcoding for now
            parameters = {
                'parameters': self._parameter_map('gsod').values(),
                'parameter_codes': self._parameter_map('gsod').keys()
            }

        return parameters

    def _parameter_map(self, service):
        if service=='ghcn-daily':
            pmap = {
                'PRCP': 'precipitation',
                'SNOW': 'snowfall',
                'SNWD': 'snow_depth',
                'TMAX': 'maximum_air_temperature',
                'TMIN': 'minimum_air_temperature',
                'TAVG': 'mean_air_temperature',
            }

        if service=='gsod':
            pmap = {
                'precip': 'precipitation',
                'snow_depth': 'snow_depth',
                'max_temp': 'maximum_air_temperature',
                'min_temp': 'minimum_air_temperature',
                'max_temp': 'mean_air_temperature',
            }

        return pmap

    def _download_data(self, feature, parameter, path, start=None, end=None, period=None):
        pass
