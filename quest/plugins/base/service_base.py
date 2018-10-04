import json
import os
import pickle

import ulmo
import param
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point

from quest import util


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


class ServiceBase(param.Parameterized):  # TODO can I make this an abc and have it be a Paramitarized?
    """Base class for data providers
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
    _parameter_map = None

    # name = param.String(default='Service', precedence=-1)

    def __init__(self, provider, **kwargs):
        self.provider = provider
        super(ServiceBase, self).__init__(**kwargs)

    @property
    def title(self):
        return '{} Download Options'.format(self.display_name)

    @property
    def use_cache(self):
        return self.provider.use_cache

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

    def get_parameters(self, catalog_ids=None):
        """Default function that should be overridden if the catalog_ids argument needs to be handled."""
        return self.parameters

    def get_download_options(self, fmt):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

        if fmt == 'param':
            schema = self

        elif fmt == 'json':
            schema = util.format_json_options(self)

        else:
            raise ValueError('{} is an unrecognized format.'.format(fmt))

        return schema

    def download(self, catalog_id, file_path, dataset, **kwargs):
        raise NotImplementedError()

    def search_catalog_wrapper(self, update_cache=False, **kwargs):
        """Get catalog_entries associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        cache_file = os.path.join(util.get_cache_dir(self.provider.name), self.name + '_catalog.p')
        if self.use_cache and not update_cache:
            try:
                catalog_entries = pd.read_pickle(cache_file)
                self._label_catalog_entries(catalog_entries)

                # convert to GeoPandas GeoDataFrame
                catalog_entries = gpd.GeoDataFrame(catalog_entries, geometry='geometry')

                return catalog_entries
            except Exception as e:
                util.logger.info(e)
                util.logger.info('updating cache')

        catalog_entries = self.search_catalog(**kwargs)

        # convert geometry into shapely objects
        if 'bbox' in catalog_entries.columns:
            catalog_entries['geometry'] = catalog_entries['bbox'].apply(lambda row: box(*[float(x) for x in row]))
            del catalog_entries['bbox']

        if {'latitude', 'longitude'}.issubset(catalog_entries.columns):
            def fn(row):
                return Point((
                    float(row['longitude']),
                    float(row['latitude'])
                ))
            catalog_entries['geometry'] = catalog_entries.apply(fn, axis=1)
            del catalog_entries['latitude']
            del catalog_entries['longitude']

        if {'geom_type', 'latitudes', 'logitudes'}.issubset(catalog_entries.columns):
            # TODO handle this case or remove from reserved fields and docs
            pass
            # del catalog_entries['geom_type']
            # del catalog_entries['latitude']
            # del catalog_entries['longitude']

        if 'geometry' in catalog_entries.columns:
            pass
            # The following line doesn't have any effect (except perhaps to validate the geometry)
            # catalog_entries['geometry'].apply(shape)

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
        catalog_entries['metadata'] = [
            {k: None if v != v else v for k, v in record.items()}
            for record in catalog_entries[extra_fields].to_dict(orient='records')
        ]
        catalog_entries.drop(extra_fields, axis=1, inplace=True)
        columns = list(set(catalog_entries.columns.tolist()).intersection(reserved_geometry_fields))
        catalog_entries.drop(columns, axis=1, inplace=True)

        params = self.get_parameters(catalog_ids=catalog_entries)
        if isinstance(params, pd.DataFrame):
            groups = params.groupby('service_id').groups
            catalog_entries['parameters'] = catalog_entries.index.map(
                lambda x: ','.join(filter(None, params.loc[groups[x]]['parameter'].tolist()))
                if x in groups.keys() else ''
            )
        else:
            catalog_entries['parameters'] = ','.join(params['parameters'])

        if self.use_cache:
            # write to cache_file
            os.makedirs(os.path.split(cache_file)[0], exist_ok=True)
            catalog_entries.to_pickle(cache_file)

        self._label_catalog_entries(catalog_entries)

        # convert to GeoPandas GeoDataFrame
        catalog_entries = gpd.GeoDataFrame(catalog_entries, geometry='geometry')

        return catalog_entries

    def _label_catalog_entries(self, catalog_entries):
        catalog_entries['service'] = util.construct_service_uri(self.provider.name, self.name)
        if 'service_id' not in catalog_entries:
            catalog_entries['service_id'] = catalog_entries.index
        catalog_entries['service_id'] = catalog_entries['service_id'].apply(str)
        catalog_entries.index = catalog_entries['service'] + '/' + catalog_entries['service_id']
        catalog_entries['name'] = catalog_entries.index

    def search_catalog(self, **kwargs):
        """
        should return a pandas dataframe or a python dictionary with
        indexed by catalog_entry uid and containing the following columns

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

    def get_tags(self, update_cache=False):
        cache_file = os.path.join(util.get_cache_dir(self.provider.name), self.name + '_tags.p')
        if self.use_cache and not update_cache:
            try:
                with open(cache_file, 'rb') as cache:
                    tags = pickle.load(cache)
                return tags
            except:
                util.logger.info('updating tag cache')

        catalog_entries = self.search_catalog_wrapper(update_cache=update_cache)
        metadata = pd.DataFrame(list(catalog_entries.metadata))

        # drop metadata fields that are unusable as tag fields
        metadata.drop(labels=['location', 'coverages'], axis=1, inplace=True, errors='ignore')

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


class TimePeriodServiceBase(ServiceBase):
    start = param.Date(default=None, precedence=2, doc='start date')
    end = param.Date(default=None, precedence=3, doc='end date')

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
    def download(self, catalog_id, file_path, dataset, **kwargs):
        service_uri = util.construct_service_uri(self.provider.name, self.name, catalog_id)
        catalog_id = self.provider.search_catalog(self.name).loc[service_uri]
        reserved = catalog_id.get('reserved')
        download_url = reserved['download_url']
        fmt = reserved.get('extract_from_zip', '')
        filename = reserved.get('filename', util.uuid('dataset'))
        file_path = self._download_file(file_path, download_url, fmt, filename)
        return {
            'file_path': file_path,
            'file_format': reserved.get('file_format'),
            'parameter': catalog_id.get('parameters'),
            'datatype': self.datatype,
        }

    def _download_file(self, path, url, tile_fmt, filename, check_modified=False):
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, 'zip'), exist_ok=True)
        tile_path = os.path.join(path, filename)
        util.logger.info('... downloading %s' % url)

        if tile_fmt == '':
            ulmo.util.download_if_new(url, tile_path, check_modified=check_modified)
        else:
            zip_path = os.path.join(path, 'zip', filename)
            ulmo.util.download_if_new(url, zip_path, check_modified=check_modified)
            util.logger.info('... ... zipfile saved at %s' % zip_path)
            tile_path = ulmo.util.extract_from_zip(zip_path, tile_path, tile_fmt)

        return tile_path