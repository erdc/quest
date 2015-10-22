from builtins import object
import abc
from future.utils import with_metaclass
from dsl import util
import pandas as pd


class WebServiceBase(with_metaclass(abc.ABCMeta, object)):
    """Base class for data services plugins
    """

    def __init__(self, use_cache=True, update_frequency='M'):
        self.use_cache = use_cache
        self.update_frequency = update_frequency
        self._register()

    def get_features(self, service):
        """Get Features associated with service.

        Take a series of query parameters and return a list of 
        locations as a geojson python dictionary
        """        
        features = self._get_features(service)
        features['external_feature_id'] = features.index
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
    def _download_data(self, feature, **kwargs):
        """
        """
