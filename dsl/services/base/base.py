from builtins import object
import abc
from future.utils import with_metaclass
from dsl import util
import os
import ulmo
import pandas as pd


class WebServiceBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data services plugins
    """

    def __init__(self, name=None, use_cache=True, update_frequency='M'):
        self.name = name
        self.use_cache = use_cache #not implemented
        self.update_frequency = update_frequency #not implemented
        self._register()

    def get_features(self, service, update_cache=False):
        """Get Features associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        cache_file = os.path.join(util.get_cache_dir(self.name), service + '_features.h5')
        if not update_cache:
            try:
                return pd.read_hdf(cache_file, 'table')
            except:
                print 'updating cache'
                pass

        features = self._get_features(service)
        params = self._get_parameters(service, features)
        if isinstance(params, pd.DataFrame):
            groups = params.groupby('_service_id').groups
            features['_parameters'] = features.index.map(lambda x: ','.join(filter(None, params.ix[groups[x]]['_parameter'].tolist())) if x in groups.keys() else '')
            features['_parameter_codes'] = features.index.map(lambda x: ','.join(filter(None, params.ix[groups[x]]['_parameter_code'].tolist())) if x in groups.keys() else '')
        else:
            features['_parameters'] = ','.join(params['_parameters'])
            features['_parameter_codes'] = ','.join(params['_parameter_codes'])

        util.mkdir_if_doesnt_exist(os.path.split(cache_file)[0])
        features.to_hdf(cache_file, 'table')
        return features

    def get_services(self):
        return self._get_services()

    def get_parameters(self, service):
        return self._get_parameters(service)

    def download(self, service, feature, save_path, **kwargs):
        return self._download(service, feature, save_path, **kwargs)

    def download_options(self, service):
        return self._download_options(service)

    @abc.abstractmethod
    def _register(self):
        """
        """

    @abc.abstractmethod
    def _get_services(self):
        """
        """

    @abc.abstractmethod
    def _get_features(self, service):
        """
        """

    @abc.abstractmethod
    def _get_parameters(self, services):
        """
        """

    @abc.abstractmethod
    def _download(self, path, service, feature, parameter, **kwargs):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

    @abc.abstractmethod
    def _download_options(self, service):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

class SingleFileBase(WebServiceBase):
    """Base file for datasets that are a single file download
    eg elevation raster etc
    """
    def _download(self, service, feature, save_path, **kwargs):
        feature = self.get_features(service).ix[feature]
        download_url = feature['_download_url']
        fmt = feature.get('_extract_from_zip', '')
        filename = feature.get('_filename', util.uuid('dataset'))
        datatype = self._get_services()[service].get('datatype')
        save_path = self._download_file(save_path, download_url, fmt, filename)
        return {
            'save_path': save_path,
            'file_format': feature.get('_file_format'),
            'parameter': feature.get('_parameters'),
            'datatype': datatype,
        }

    def _download_options(self, service):
        return {}

    def _download_file(self, path, url, tile_fmt, filename, check_modified=False):
        util.mkdir_if_doesnt_exist(path)
        util.mkdir_if_doesnt_exist(os.path.join(path, 'zip'))
        tile_path = os.path.join(path, filename)
        print('... downloading %s' % url)
        if tile_fmt == '':
            ulmo.util.download_if_new(url, tile_path, check_modified=check_modified)
        else:
            zip_path = os.path.join(path, 'zip', filename)
            ulmo.util.download_if_new(url, zip_path, check_modified=check_modified)
            print('... ... zipfile saved at %s' % zip_path)
            tile_path = ulmo.util.extract_from_zip(zip_path, tile_path, tile_fmt)

        return tile_path
