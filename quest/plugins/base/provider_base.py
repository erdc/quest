import abc
from quest import util
import os
import pickle
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point, shape
from quest.util.log import logger
from quest.database.database import get_db, db_session
import json

reserved_catalog_entry_fields = [
    'name',
    'service',
    'service_id',
    'publisher_id',
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

reserved_catalog_entry_fields.extend(reserved_geometry_fields)


class ProviderBase(metaclass=abc.ABCMeta):
    """Base class for data provider plugins
    """
    service_list = None
    publisher_list = None
    display_name = None
    description = None
    organization_name = None
    organization_abbr = None

    @property
    def services(self):
        if self.service_list is None:
            return {}
        if self._services is None:
            self._services = {s.service_name: s(name=s.service_name, provider=self) for s in self.service_list}

        return self._services

    @property
    def publishers(self):
        if self.publisher_list is None:
            return {}
        if self._publishers is None:
            self._publishers = {p.publisher_name: p(name=p.publisher_name, provider=self) for p in self.publisher_list}

        return self._publishers

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
    def credentials(self):
        if self._credentials is None:
            db = get_db()
            with db_session:
                p = db.Providers.select().filter(provider=self.name).first()
                if p is None:
                    raise ValueError('The {0} Provider has not been authenticated yet. Please call quest.api.authenticate_provider({0})'.format(self.name))
                else:
                    self._credentials = dict(username=p.username, password=p.password)

        return self._credentials

    def __init__(self, name=None, use_cache=True, update_frequency='M'):
        self.use_cache = use_cache #not implemented
        self.update_frequency = update_frequency #not implemented
        self._services = None
        self._publishers = None
        self._credentials = None

    def search_catalog(self, service, update_cache=False, **kwargs):
        """Get catalog_entries associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        cache_file = os.path.join(util.get_cache_dir(self.name), service + '_catalog.p')
        if self.use_cache and not update_cache:
            try:
                catalog_entries = pd.read_pickle(cache_file)
                self._label_entries(catalog_entries, service)

                # convert to GeoPandas GeoDataFrame
                catalog_entries = gpd.GeoDataFrame(catalog_entries, geometry='geometry')

                return catalog_entries
            except Exception as e:
                logger.info(e)
                logger.info('updating cache')

        catalog_entries = self.services[service].search_catalog(**kwargs)

        # convert geometry into shapely objects
        if 'bbox' in catalog_entries.columns:
            catalog_entries['geometry'] = catalog_entries['bbox'].apply(lambda row: box(*[float(x) for x in row]))
            del catalog_entries['bbox']

        if {'latitude', 'longitude'}.issubset(catalog_entries.columns):
            fn = lambda row: Point((
                                    float(row['longitude']),
                                    float(row['latitude'])
                                    ))
            catalog_entries['geometry'] = catalog_entries.apply(fn, axis=1)
            del catalog_entries['latitude']
            del catalog_entries['longitude']

        if {'geom_type', 'latitudes', 'logitudes'}.issubset(catalog_entries.columns):
            # TODO handle this case or remove from reserved fields and docs
            pass
            # del features['geom_type']
            # del features['latitude']
            # del features['longitude']

        if 'geometry' in catalog_entries.columns:
            catalog_entries['geometry'].apply(shape)

        if 'geometry' not in catalog_entries.columns:
            catalog_entries['geometry'] = None

        # add defaults values
        if 'display_name' not in catalog_entries.columns:
            catalog_entries['display_name'] = catalog_entries.index

        if 'description' not in catalog_entries.columns:
            catalog_entries['description'] = ''

        # merge extra data columns/fields into metadata as a dictionary
        extra_fields = list(set(catalog_entries.columns.tolist()) - set(reserved_catalog_entry_fields))
        # change NaN to None so it can be JSON serialized properly
        catalog_entries['metadata'] = [{k: None if v != v else v for k, v in record.items()}
                                for record in catalog_entries[extra_fields].to_dict(orient='records')]
        catalog_entries.drop(extra_fields, axis=1, inplace=True)
        columns = list(set(catalog_entries.columns.tolist()).intersection(reserved_geometry_fields))
        catalog_entries.drop(columns, axis=1, inplace=True)

        params = self.get_parameters(service=service, catalog_ids=catalog_entries)
        if isinstance(params, pd.DataFrame):
            groups = params.groupby('service_id').groups
            catalog_entries['parameters'] = catalog_entries.index.map(lambda x: ','.join(filter(None, params.loc[groups[x]]['parameter'].tolist())) if x in groups.keys() else '')
        else:
            catalog_entries['parameters'] = ','.join(params['parameters'])

        if self.use_cache:
            # write to cache_file
            os.makedirs(os.path.split(cache_file)[0], exist_ok=True)
            catalog_entries.to_pickle(cache_file)

        self._label_catalog_entries(catalog_entries, service)

        # convert to GeoPandas GeoDataFrame
        catalog_entries = gpd.GeoDataFrame(catalog_entries, geometry='geometry')

        return catalog_entries

    def _label_catalog_entries(self, catalog_entries, service):
        catalog_entries['service'] = util.construct_service_uri(self.name, service)
        if 'service_id' not in catalog_entries:
            catalog_entries['service_id'] = catalog_entries.index
        catalog_entries['service_id'] = catalog_entries['service_id'].apply(str)
        catalog_entries.index = catalog_entries['service'] + '/' + catalog_entries['service_id']
        catalog_entries['name'] = catalog_entries.index

    def get_tags(self, service, update_cache=False):
        cache_file = os.path.join(util.get_cache_dir(self.name), service + '_tags.p')
        if self.use_cache and not update_cache:
            try:
                with open(cache_file, 'rb') as cache:
                    tags = pickle.load(cache)
                return tags
            except:
                logger.info('updating tag cache')

        catalog_entries = self.search_catalog(service=service, update_cache=update_cache)
        metadata = pd.DataFrame(list(catalog_entries.metadata))

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

    def get_publishers(self):
        return {k: v.metadata for k, v in self.publishers.items()}

    def get_parameters(self, service, catalog_ids=None):
        return self.services[service].get_parameters(catalog_ids=catalog_ids)

    def download(self, service, catalog_id, file_path, dataset, **kwargs):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """
        return self.services[service].download(catalog_id, file_path, dataset, **kwargs)

    def get_download_options(self, service, fmt):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """
        return self.services[service].get_download_options(fmt)

    def publish(self, publisher, **kwargs):
        return self.publishers[publisher].publish(**kwargs)

    def publish_options(self, publisher, fmt):
        return self.publishers[publisher].publish_options(fmt)

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