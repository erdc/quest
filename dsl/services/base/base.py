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

    def __init__(self, uid=None, use_cache=True, update_frequency='M'):
        self.uid = uid
        self.use_cache = use_cache #not implemented
        self.update_frequency = update_frequency #not implemented
        self._register()

    def get_features(self, service, update_cache=False):
        """Get Features associated with service.

        Take a series of query parameters and return a list of
        locations as a geojson python dictionary
        """
        cache_file = os.path.join(util.get_cache_dir(self.uid), service + '_features.h5')
        if not update_cache:
            try:
                return pd.read_hdf(cache_file, 'table')
            except:
                print 'updating cache'
                pass

        features = self._get_features(service)
        features['_name_'] = features.index
        params = self._get_parameters(service, features)
        if isinstance(params, pd.DataFrame):
            groups = params.groupby('_name_').groups
            features['_parameters_'] = features.index.map(lambda x: ','.join(filter(None, params.ix[groups[x]]['_parameter_'].tolist())) if x in groups.keys() else '')
            features['_parameter_codes_'] = features.index.map(lambda x: ','.join(filter(None, params.ix[groups[x]]['_parameter_code_'].tolist())) if x in groups.keys() else '')
        else:
            features['_parameters_'] = ','.join(params['_parameters_'])
            features['_parameter_codes_'] = ','.join(params['_parameter_codes_'])

        # peewee datasets cannot store field names with _id in them so rename
        # fields to _uid
        r = {field: field.replace('_id', '_uid') for field in features.columns}
        if 'id' in r.keys():
            r['id'] = 'uid'
        features.rename(columns=r, inplace=True)

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
        download_url = feature['_download_url_']
        extract_from_zip = feature.get('_extract_from_zip_', '')
        save_path = ulmo.util.download_tiles(save_path, [download_url],
                                             extract_from_zip)[0]
        return {
            'save_path': save_path,
            'file_format': feature.get('_file_format_'),
            'parameter': feature.get('_parameter_'),
        }

    def _download_options(self, service):
        return {}
