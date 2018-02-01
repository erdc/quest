from builtins import object
import abc
from future.utils import with_metaclass
from quest import util
import os
import pickle
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point, shape
from quest.util.log import logger
from ...api.database import get_db, db_session, select_features
import json

reserved_feature_fields = [
    'name',
    'service',
    'service_id',
    'display_name',
    'description',
    'reserved',
    'geometry',
    'parameters',

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
            self._services = {s.service_name: s(name=s.service_name, provider=self)
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

    @property
    def auth(self):
        if self._auth is None:
            db = get_db()
            with db_session:
                p = db.Providers.select().filter(provider=self.name).first()
                if p is None:
                    raise ValueError('The {0} Provider has not been authenticated yet. Please call quest.api.authenticate_provider({0})'.format(self.name))
                else:
                    self._auth = dict(username=p.username, password=p.password)

    def __init__(self, name=None, use_cache=True, update_frequency='M'):
        self.name = name
        self.use_cache = use_cache #not implemented
        self.update_frequency = update_frequency #not implemented
        self._services = None
        self._auth = None

    def get_features(self, service, update_cache=False, **kwargs):
        """Get Features associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        cache_file = os.path.join(util.get_cache_dir(self.name), service + '_features.p')
        if self.use_cache and not update_cache:
            try:
                features = pd.read_pickle(cache_file)
                self._label_features(features, service)

                # convert to GeoPandas GeoDataFrame
                features = gpd.GeoDataFrame(features, geometry='geometry')

                return features
            except Exception as e:
                logger.info(e)
                logger.info('updating cache')

        # get features from service
        features = self.services[service].get_features(**kwargs)

        # convert geometry into shapely objects
        if 'bbox' in features.columns:
            features['geometry'] = features['bbox'].apply(lambda row: box(*[float(x) for x in row]))
            del features['bbox']

        if {'latitude', 'longitude'}.issubset(features.columns):
            fn = lambda row: Point((
                                    float(row['longitude']),
                                    float(row['latitude'])
                                    ))
            features['geometry'] = features.apply(fn, axis=1)
            del features['latitude']
            del features['longitude']

        if {'geom_type', 'latitudes', 'logitudes'}.issubset(features.columns):
            # TODO handle this case or remove from reserved fields and docs
            pass
            # del features['geom_type']
            # del features['latitude']
            # del features['longitude']

        if 'geometry' in features.columns:
            features['geometry'].apply(shape)

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

        if self.use_cache:
            # write to cache_file
            util.mkdir_if_doesnt_exist(os.path.split(cache_file)[0])
            features.to_pickle(cache_file)

        self._label_features(features, service)

        # convert to GeoPandas GeoDataFrame
        features = gpd.GeoDataFrame(features, geometry='geometry')

        return features

    def _label_features(self, features, service):
        features['service'] = util.construct_service_uri(self.name, service)
        if 'service_id' not in features:
            features['service_id'] = features.index
        features['service_id'] = features['service_id'].apply(str)
        features.index = features['service'] + '/' + features['service_id']
        features['name'] = features.index

    def get_tags(self, service, update_cache=False):

        cache_file = os.path.join(util.get_cache_dir(self.name), service + '_tags.p')
        if self.use_cache and not update_cache:
            try:
                with open(cache_file, 'rb') as cache:
                    tags = pickle.load(cache)
                return tags
            except:
                logger.info('updating tag cache')

        features = self.get_features(service=service, update_cache=update_cache)
        metadata = pd.DataFrame(list(features.metadata))

        # drop metadata fields that are unusable as tag fields
        metadata.drop(labels=['location'], axis=1, inplace=True, errors='ignore')

        tags = {}
        for tag in metadata.columns:
            try:
                tags[tag] = list(metadata[tag].unique())

                # make sure datetime values are serialized (for RPC server)
                tags[tag] = json.loads(json.dumps(tags[tag], default=util.to_json_default_handler))
            except TypeError:
                values = list(metadata[tag])
                new_tags = dict()
                new_tags[tag] = list()
                for v in values:
                    if isinstance(v, dict):
                        self._combine_dicts(new_tags, self._get_tags_from_dict(tag, v))
                    else:
                        new_tags[tag].append(v)
                if not new_tags[tag]:
                    del new_tags[tag]
                tags.update({k: list(set(v)) for k, v in new_tags.items()})

        if self.use_cache:
            # write to cache_file
            with open(cache_file, 'wb') as cache:
                pickle.dump(tags, cache)

        return tags

    def _get_tags_from_dict(self, tag, d):
        """Helper function for `get_tags` to recursively parse dicts and add them as multi-indexed tags
        """
        tags = dict()
        for k, v in d.items():
            new_tag = '{}:{}'.format(tag, k)
            if isinstance(v, dict):
                self._combine_dicts(tags, self._get_tags_from_dict(new_tag, v))
            else:
                tags[new_tag] = v

        return tags

    def _combine_dicts(self, this, other):
        """Helper function for `get_tags` to combine dictionaries by aggregating values rather than overwriting them.
        """
        for k, other_v in other.items():
            other_v = util.listify(other_v)
            if k in this:
                this_v = this[k]
                if isinstance(this_v, list):
                    other_v.extend(this_v)
                else:
                    other_v.append(this_v)
            this[k] = other_v

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

    def authenticate_me(self, **kwargs):
        raise NotImplementedError

    def unauthenticate_me(self):
        db = get_db()
        with db_session:
            p = db.Providers.select().filter(provider=self.name).first()
            if p is None:
                raise ValueError('Provider does not exist in the database.')
            else:
                p.delete()