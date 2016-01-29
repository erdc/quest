"""DSL wrapper for NCDC GHCN and GSOD Services."""
from .base import WebServiceBase
import pandas as pd
from ulmo.ncdc import ghcn_daily, gsod
from ulmo.ncdc.ghcn_daily.core import _get_inventory as _get_ghcn_inventory


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

        # remove locations with invalid coordinates
        valid = pd.notnull(features.latitude) & pd.notnull(features.longitude)
        features = features[valid]
        features['geom_type'] = 'Point'
        features['geom_coords'] = \
            zip(features['longitude'], features['latitude'])
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
                'PRCP': 'rainfall:daily:total',
                'SNOW': 'snowfall:daily:total',
                'SNWD': 'snow_depth:daily:total',
                'TMAX': 'air_temperature:daily:total',
                'TMIN': 'air_temperature:daily:minimum',
                'TAVG': 'air_temperature:daily:mean',
            }

            #// NOTE // consider switching order. store on disk as feature->dataset
            #, then parameter/units become part of dataset metadata.

        if service=='gsod':
            pmap = {
                'precip': 'rainfall:daily:total',
                'snow_depth': 'snow_depth:daily:total',
                'max_temp': 'air_temperature:daily:max',
                'min_temp': 'air_temperature:daily:min',
                'max_temp': 'air_temperature:daily:min',
            }

        return pmap

    def _download_dataset(self, path, service, feature, **kwargs):
        pass

    def _download_dataset_options(self, service):
        pass
