from builtins import object
import abc
from future.utils import with_metaclass
from quest import util
import os
import ulmo
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point, Polygon, LineString, shape
from quest.util.log import logger
from quest.util.param_util import format_json_options
import json
import param

reserved_feature_fields = [
    'display_name',
    'description',
    'reserved',
    'geometry',

]
reserved_geometry_fields = [
    'latitude',
    'longitude',
    'geom_type',
    'latitudes',
    'longitudes',
    'bbox',
]

reserved_feature_fields.extend(reserved_geometry_fields)


class ProviderBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data provider plugins
    """
    service_base_class = None
    display_name = None
    description = None
    organization_name = None
    organization_abbr = None

    @property
    def services(self):
        if self.service_base_class is None:
            return {}  # TODO or should I raise a NotImplementedError
        if self._services is None:
            self._services = {s.service_name: s(name=s.service_name)
                              for s in self.service_base_class.__subclasses__()}
        return self._services

    @property
    def metadata(self):
        return {
            'display_name': self.display_name,
            'description': self.description,
            'organization': {
                'abbr': self.organization_abbr,
                'name': self.organization_name,
            }
        }

    def __init__(self, name=None, use_cache=True, update_frequency='M'):
        self.name = name
        self.use_cache = use_cache #not implemented
        self.update_frequency = update_frequency #not implemented
        self._services = None

    def get_features(self, service, update_cache=False, **kwargs):
        """Get Features associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        cache_file = os.path.join(util.get_cache_dir(self.name), service + '_features.geojson')
        if not update_cache:
            try:
                features = gpd.read_file(cache_file)
                features.set_index('id', inplace=True)
                return features
            except:
                logger.info('updating cache')
                pass

        # get features from service
        features = self.services[service].get_features(**kwargs)

        # convert geometry into shapely objects
        if 'bbox' in features.columns:
            features['geometry'] = features['bbox'].apply(lambda row: box(*[float(x) for x in row]))
            del features['bbox']

        if all(x in features.columns for x in ['latitude', 'longitude']):
            fn = lambda row: Point((
                                    float(row['longitude']),
                                    float(row['latitude'])
                                    ))
            features['geometry'] = features.apply(fn, axis=1)
            features['geometry'] = features.apply(fn, axis=1)

        if 'geometry' in features.columns:
            # TODO
            # check for geojson str or shapely object
            pass

        # if no geometry fields are found then this is a geotypical feature
        if 'geometry' not in features.columns:
            features['geometry'] = None

        # add defaults values
        if 'display_name' not in features.columns:
            features['display_name'] = features.index

        if 'description' not in features.columns:
            features['description'] = ''

        # merge extra data columns/fields into metadata as a dictionary
        extra_fields = list(set(features.columns.tolist()) - set(reserved_feature_fields))
        # change NaN to None so it can be JSON serialized properly
        features['metadata'] = [{k: None if v != v else v for k, v in record.items()}
                                for record in features[extra_fields].to_dict(orient='records')]
        features.drop(extra_fields, axis=1, inplace=True)
        columns = list(set(features.columns.tolist()).intersection(reserved_geometry_fields))
        features.drop(columns, axis=1, inplace=True)

        params = self.get_parameters(service, features)
        if isinstance(params, pd.DataFrame):
            groups = params.groupby('service_id').groups
            features['parameters'] = features.index.map(lambda x: ','.join(filter(None, params.loc[groups[x]]['parameter'].tolist())) if x in groups.keys() else '')
            # features['parameter_codes'] = features.index.map(lambda x: ','.join(filter(None, params.loc[groups[x]]['_parameter_code'].tolist())) if x in groups.keys() else '')
        else:
            features['parameters'] = ','.join(params['parameters'])
            # features['parameter_codes'] = ','.join(params['parameter_codes'])

        # convert to GeoPandas GeoDataFrame
        features = gpd.GeoDataFrame(features, geometry='geometry')

        # write to cache_file
        util.mkdir_if_doesnt_exist(os.path.split(cache_file)[0])
        with open(cache_file, 'w') as f:
            f.write(features.to_json(default=util.to_json_default_handler))

        return features

    def get_services(self):
        return {k: v.metadata for k, v in self.services.items()}

    def get_parameters(self, service, features=None):
        return self.services[service].get_parameters(features=features)

    def download(self, service, feature, file_path, dataset, **kwargs):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """
        return self.services[service].download(feature, file_path, dataset, **kwargs)

    def download_options(self, service, fmt):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """
        return self.services[service].download_options(fmt)


# base class for services
# TODO can I make this an abc and have it be a Paramitarized?
class ServiceBase(param.Parameterized):
    """Base class for data services
    """
    service_name = None
    display_name = None
    description = None
    service_type = None
    unmapped_parameters_available = None
    geom_type = None
    datatype = None
    geographical_areas = None
    bounding_boxes = None
    smtk_template = None
    _parameter_map = None

    name = param.String(default='Service', precedence=-1)

    @property
    def title(self):
        return '{} Download Options'.format(self.display_name)

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
        if hasattr(self, 'parameter'):
            pmap = self.parameter_map(invert=True)
            return pmap[self.parameter]

    def parameter_map(self, invert=False):
        pmap = self._parameter_map

        if pmap is None:
            raise NotImplementedError()

        if invert:
            pmap = {v: k for k, v in pmap.items()}

        return pmap

    def get_parameters(self, features=None):
        """Default function that should be overridden if the features argument needs to be handled."""
        return self.parameters

    def download_options(self, fmt):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

        if fmt == 'param':
            schema = self

        elif fmt == 'smtk':
            if self.smtk_template is None:
                return ''
            parameters = sorted(self.parameters['parameters'])
            parameters = [(p.capitalize(), p) for p in parameters]
            schema = util.build_smtk('download_options',
                                     self.smtk_template,
                                     title=self.title,
                                     parameters=parameters)

        elif fmt == 'json':
            schema = format_json_options(self)

        else:
            raise ValueError('{} is an unrecognized format.'.format(fmt))

        return schema

    def download(self, feature, file_path, dataset, **params):
        raise NotImplementedError()

    def get_features(self, **kwargs):
        """
        should return a pandas dataframe or a python dictionary with
        indexed by feature uid and containing the following columns

        reserved column/field names
            display_name -> will be set to uid if not provided
            description -> will be set to '' if not provided
            download_url -> optional download url

            defining geometry options:
                1) geometry -> geojson string or shapely object
                2) latitude & longitude columns/fields
                3) geometry_type, latitudes, longitudes columns/fields
                4) bbox column/field -> tuple with order (lon min, lat min, lon max, lat max)

        all other columns/fields will be accumulated in a dict and placed
        in a metadata field.
        :param **kwargs:

        """
        raise NotImplementedError()


class TimePeriodServiceBase(ServiceBase):
    start = param.Date(default=None, precedence=2, doc='start date')
    end = param.Date(default=None, precedence=3, doc='end date')
    smtk_template = 'start_end.sbt'

    @property
    def start_string(self):
        return self.start.strftime('%Y-%m-%d')

    @property
    def end_string(self):
        return self.end.strftime('%Y-%m-%d')


# abc
class SingleFileServiceBase(ServiceBase):
    """Base file for datasets that are a single file download
    eg elevation raster etc
    """
    def download(self, feature, file_path, dataset, **params):
        feature = self.get_features().loc[feature]
        reserved = feature.get('reserved')
        download_url = reserved['download_url']
        fmt = reserved.get('extract_from_zip', '')
        filename = reserved.get('filename', util.uuid('dataset'))
        file_path = self._download_file(file_path, download_url, fmt, filename)
        return {
            'file_path': file_path,
            'file_format': reserved.get('file_format'),
            'parameter': feature.get('parameters'),
            'datatype': self.datatype,
        }

    def _download_file(self, path, url, tile_fmt, filename, check_modified=False):
        util.mkdir_if_doesnt_exist(path)
        util.mkdir_if_doesnt_exist(os.path.join(path, 'zip'))
        tile_path = os.path.join(path, filename)
        logger.info('... downloading %s' % url)

        if tile_fmt == '':
            ulmo.util.download_if_new(url, tile_path, check_modified=check_modified)
        else:
            zip_path = os.path.join(path, 'zip', filename)
            ulmo.util.download_if_new(url, zip_path, check_modified=check_modified)
            logger.info('... ... zipfile saved at %s' % zip_path)
            tile_path = ulmo.util.extract_from_zip(zip_path, tile_path, tile_fmt)

        return tile_path