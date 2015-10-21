from builtins import object
import abc
from future.utils import with_metaclass
from dsl import util
import ulmo
import pandas as pd


class WebServiceBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data services plugins
    """

    def __init__(self, cache_dir=None, use_cache=True, update_frequency='M'):
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        self.update_frequency = update_frequency
        self._register()

    def get_features(self, service):
        """Get Features associated with service.

        Take a series of query parameters and return a list of 
        locations as a geojson python dictionary
        """        
        features = self._get_features(service)
        params = self._get_parameters(service, features)
        if isinstance(params, pd.DataFrame):
            groups = params.groupby('feature_id').groups
            features['parameters'] = features.index.map(lambda x: ','.join(filter(None, params.ix[groups[x]]['parameter'].tolist())) if x in groups.keys() else '')
            features['parameter_codes'] = features.index.map(lambda x: ','.join(filter(None, params.ix[groups[x]]['parameter_code'].tolist())) if x in groups.keys() else '')
        else:
            features['parameters'] = ','.join(params['parameters'])
            features['parameter_codes'] = ','.join(params['parameter_codes'])

        return features

    def get_services(self, filters={}):
        return self._get_services()

    def get_parameters(self, service, features=None):
        return self._get_parameters(service)

    def download_dataset(self, path, service, feature, parameter, **kwargs):
        return self._download_dataset(path, service, feature, parameter, **kwargs)

    def download_dataset_options(self, service):
        return self._download_dataset_options()

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
    def _download_dataset(self, path, service, feature, parameter, **kwargs):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

    @abc.abstractmethod
    def _download_dataset_options(self, service):
        """
        needs to return dictionary
        eg. {'path': /path/to/dir/or/file, 'format': 'raster'}
        """

class SingleFileBase(WebServiceBase):
    """Base file for datasets that are a single file download
    eg elevation raster etc
    """
    def _download_dataset(self, path, service, feature, parameter, **kwargs):
        feature = self.get_features(service)[feature]
        download_url = feature['download_url']
        extract_from_zip = feature.get('extract_from_zip', '')
        save_path = ulmo.util.download_tiles(path, [download_url], extract_from_zip)[0]
        return {'save_path': save_path, 'file_format': feature.get('file_format')}
        
    def _download_dataset_options(self, service):
        return {}

